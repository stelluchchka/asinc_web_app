from contextvars import ContextVar
import hashlib
import hmac
import json
import jwt

from sanic.request import Request
from sanic.response import HTTPResponse, json, text
from sanic.views import HTTPMethodView
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload

from config import *
from database import async_session, async_engine
from models import User, Account, Transaction, Base
from auth_utils import generate_jwt, isAdmin

_base_model_session_ctx = ContextVar("session")

@app.listener("before_server_start")
async def create_table(app):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@app.middleware("request")
async def check_jwt(request: Request):
    auth_header = request.headers.get('Authorization')
    if auth_header:
        token = auth_header.split()[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.ctx.user_id = payload['user_id']
            request.ctx.isAdmin = payload['isAdmin']
        except jwt.PyJWTError:
            pass

@app.middleware("request")
async def inject_session(request):
    try:
        request.ctx.session = async_session
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)
        # print(request.ctx.session)
    except Exception as e:
        print(f"Ошибка: {e}")
        raise

@app.middleware("response")
async def close_session(request, response):
    try:
        if hasattr(request.ctx, "session_ctx_token"):
            _base_model_session_ctx.reset(request.ctx.session_ctx_token)
            # request.ctx.session.close()
    except Exception as e:
        print(f"Ошибка: {e}")
        raise

@app.post("/add_user", ignore_body=False)
async def add_user(request):
    try:
        data = request.json
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        if not full_name or not password or not email:
            return json({'error': 'full_name or password or email missing'}, status=400)
        try:
            async with request.ctx.session.begin() as conn:
                stmt = select(User).where(User.email.in_([email]))
                user_result = await conn.execute(stmt)
                user = user_result.scalar_one_or_none()
                if (user):
                    return json({'message': "Ошибка при создании пользователя: пользователь с такой почтой уже зарегистрирован"}, status=400)
                acc = Account(balance=0)
                user = User(full_name=full_name, email=email, password=password, accounts=[acc])
                conn.add(user)
                await conn.commit()
            return json({'message': user.info()}, status=200)
        except Exception as e:
            return json({'message': f"Ошибка при создании пользователя: {e}"}, status=400)
    except:
        return json({'error': 'Invalid JSON'}, status=400)

@app.post("/add_admin", ignore_body=False)
async def add_admin(request):
    try:
        data = request.json
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        if not full_name or not password or not email:
            return json({'error': 'full_name or password or email missing'}, status=400)
        try:
            async with request.ctx.session.begin() as conn:
                stmt = select(User).where(User.email.in_([email]))
                user_result = await conn.execute(stmt)
                user = user_result.scalar_one_or_none()
                if (user):
                    return json({'message': "Ошибка при создании администратора: вы уже зарегистрированы"}, status=400)
                user = User(full_name=full_name, email=email, password=password, isAdmin=True)
                conn.add(user)
                await conn.commit()
            return json({'message': user.info()}, status=200)
        except Exception as e:
            return json({'message': f"Ошибка при создании администратора: {e}"}, status=400)
    except:
        return json({'error': 'Invalid JSON'}, status=400)

@app.get("/login", ignore_body=False)
async def login(request):
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        if not password or not email:
            return json({'error': 'password or email missing'}, status=400)
        try:
            async with request.ctx.session.begin() as conn:
                # session = request.ctx.session
                stmt = select(User).where(User.email.in_([email]))
                user_result = await conn.execute(stmt)
                user = user_result.scalar_one_or_none()
                if (user and user.password == password):
                    token = generate_jwt({'id': user.id, 'isAdmin': user.isAdmin})
                    return json({'token': token}, status=200)
        except Exception as e:
            return json({'message': f"Ошибка при идентификации пользователя: {e}"}, status=400)
    except:
        return json({'error': 'Invalid JSON'}, status=400)

@app.get("/user_info")
async def get_user_info(request):
    try:
        user_id = request.ctx.user_id
        session = request.ctx.session
        async with session.begin() as conn:
            stmt = select(User).where(User.id == user_id)
            result = await conn.execute(stmt)
            user = result.scalar_one()
            return json(user.info())
    except Exception as e:
        return json({'message': f"Ошибка при нахождении пользователя: {e}"}, status=400)

@app.get("/accounts_info")
async def get_accounts_info(request):
    try:
        user_id = request.ctx.user_id
        session = request.ctx.session
        async with session.begin() as conn:
            stmt = select(Account).where(Account.id_user == user_id)
            result = await conn.execute(stmt)
            accounts = result.scalars().all()
            accounts_dicts = [account.info() for account in accounts]
            return json(accounts_dicts)
    except Exception as e:
        return json({'message': f"Ошибка при нахождении счетов: {e}"}, status=400)

class UsersView(HTTPMethodView):
    decorators=[isAdmin]
    async def get(self, request):
        try:
            session = request.ctx.session
            async with session.begin() as conn:
                stmt = select(User).options(selectinload(User.accounts)).where(User.isAdmin == False)
                result = await conn.execute(stmt)
                users = result.scalars().all()
                users_dicts = [user.full_info() for user in users]
                return json(users_dicts)
        except Exception as e:
            return json({'message': f"Ошибка при нахождении пользователя: {e}"}, status=400)
    async def post(self, request):
        resp = await add_user(request)
        return resp
app.add_route(UsersView.as_view(), "/users")

class UserView(HTTPMethodView):
    decorators=[isAdmin]
    async def delete(self, request, id):
        try:
            id = int(id)
            session = request.ctx.session
            async with session.begin() as conn:
                stmt = select(User).where(and_(User.id == id, User.isAdmin == False))
                result = await conn.execute(stmt)
                user_to_delete = result.scalar_one_or_none()
                if not user_to_delete:
                    return json({'message': "Пользователь не найден или является администратором"}, status=404)
                await conn.execute(delete(User).where(User.id == id))
                await conn.commit()
                return text("Пользователь удален", status=200)
        except Exception as e:
            return json({'message': f"Ошибка при удалении пользователя: {e}"}, status=400)
    async def patch(self, request, id):
        try:
            id = int(id)
            session = request.ctx.session
            update_data = request.json
            async with session.begin() as conn:
                stmt = select(User).options(selectinload(User.accounts)).where(User.id == id)
                result = await conn.execute(stmt)
                user = result.scalar_one_or_none()
                if not user:
                    return json({'message': "Пользователь не найден"}, status=404)                
                for key, value in update_data.items():
                    if key != 'accounts':
                        setattr(user, key, value)
                if 'accounts' in update_data:
                    new_accounts_data = update_data['accounts']
                    user.accounts.clear()
                    for account_data in new_accounts_data:
                        new_account = Account(balance=account_data['balance'])
                        user.accounts.append(new_account)
                await conn.commit()
            return json({'message': "Пользователь успешно обновлен"}, status=200)
        except Exception as e:
            return json({'message': f"Ошибка при обновлении пользователя: {str(e)}"}, status=400)

app.add_route(UserView.as_view(), "/users/<id>")

@app.post('/handle_webhook')
async def handle_webhook(request):
    body = request.json
    signature = body.get('signature')
    message = ''.join(f'{v}' for k, v in sorted(body.items()) if k != "signature") + SECRET_KEY
    calculated_signature = hashlib.sha256(message.encode()).hexdigest()[:64]
    if signature != calculated_signature:
        return json({"message" : f"Invalid signature"}, status=403)
    try:
        account_id = body.get('account_id')
        user_id = body.get('user_id')
        transaction_id = body.get('transaction_id')
        amount = body.get('amount')
        session = request.ctx.session
        async with session.begin() as conn:
            stmt = select(User).options(selectinload(User.accounts)).where(User.id == user_id)
            result = await conn.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return json({'message': "Пользователь не найден"}, status=404)
            stmt = select(Transaction).where(Transaction.id.in_([transaction_id]))
            result = await conn.execute(stmt)
            transaction = result.scalar_one_or_none()
            if transaction:
                return json({'message': "поле id транзакции должно быть уникально"}, status=404)
            stmt = select(Account).where(and_(Account.id_user == user_id, Account.id == account_id))
            result = await conn.execute(stmt)
            account = result.scalar_one_or_none()
            if account == None:
                new_account = Account(balance=amount)
                user.accounts.append(new_account)
                conn.add(new_account)
            else:
                account.balance = account.balance + amount
            new_transaction = Transaction(id=transaction_id, summ=amount)
            conn.add(new_transaction)
            conn.commit()
    except Exception as e:
        return json({'message': f"Ошибка при выполнении транзакции: {str(e)}"}, status=400)
    return json({"message" : f"Транзакция успешно выполнена, {message}"}, status=200)

@app.route('/test', ignore_body=False)
async def test(request):
    user_id = request.ctx.user_id
    isAdmin = request.ctx.isAdmin
    if user_id is None:
        return json({'error': 'Unauthorized'}, status=401)
    message = f"Welcome, user {user_id}"
    if (isAdmin):
        message = message + "\nyou are admin"
    return json({"message": message}, status=200)

if __name__ == '__main__':
    # asyncio.run(create_table())
    app.run(host='0.0.0.0', port=8000, debug=True)