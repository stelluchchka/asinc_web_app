import asyncio
from contextvars import ContextVar

from sanic.response import json, text
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import *
from database import async_session, _base_model_session_ctx, create_table
from models import User, Account, Transaction

_base_model_session_ctx = ContextVar("session")

@app.middleware("request")
async def inject_session(request):
    try:
        request.ctx.session = async_session
        request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)
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


@app.get("/add_user")
async def create_user(request):
    try:
        async with request.ctx.session.begin() as conn:
            acc = Account(balance=0)
            user = User(full_name="name", email="example@h.t", password='123', accounts=[acc])
            conn.add_all([user])
            await conn.commit()
        return json(user.to_dict())
    except Exception as e:
        print(f"Ошибка при создании пользователя: {e}")
        return text("error")

@app.get("/user/<pk:int>")
async def get_user(request, pk):
    session = request.ctx.session
    async with session.begin() as conn:
        stmt = select(User).where(User.id == pk).options(selectinload(User.accounts))
        result = await conn.execute(stmt)
        user = result.scalar_one()
    if not user:
        return json({})
    return json(user.to_dict())

if __name__ == '__main__':
    asyncio.run(create_table())
    app.run(host='0.0.0.0', port=8000, debug=True)