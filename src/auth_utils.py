import jwt
from datetime import datetime, timedelta
from config import SECRET_KEY 
from sanic.request import Request
from sanic.response import HTTPResponse
def generate_jwt(user_data):
    payload = {
        'user_id': user_data['id'],
        'isAdmin': user_data['isAdmin'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def admin_required(f):
    async def wrapper(request: Request, *args, **kwargs):
        if not request.ctx.isAdmin:
            return HTTPResponse(body="Access denied", status=403)
        return await f(request, *args, **kwargs)
    return wrapper