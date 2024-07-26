import jwt
from datetime import datetime, timedelta
from config import SECRET_KEY
from sanic.request import Request
from sanic.response import HTTPResponse


def generate_jwt(user_data):
    payload = {
        "user_id": user_data["id"],
        "isAdmin": user_data["isAdmin"],
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def invalidate_jwt(token):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    new_payload = {
        "user_id": payload["user_id"],
        "isAdmin": payload["isAdmin"],
        "exp": datetime.utcnow(),
    }
    token = jwt.encode(new_payload, SECRET_KEY, algorithm="HS256")
    return token


def isAdmin(f):
    async def wrapper(request: Request, *args, **kwargs):
        if not request.ctx.isAdmin:
            return HTTPResponse(body="Access denied", status=403)
        return await f(request, *args, **kwargs)

    return wrapper


def isUser(f):
    async def wrapper(request: Request, *args, **kwargs):
        if not hasattr(request.ctx, "user_id"):
            return HTTPResponse(body="Access denied", status=403)
        return await f(request, *args, **kwargs)

    return wrapper
