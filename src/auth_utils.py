import jwt
from datetime import datetime, timedelta
from config import SECRET_KEY
from sanic.request import Request
from sanic.response import HTTPResponse
import hashlib


salt = "some_salt:)"


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
        if not hasattr(request.ctx, "isAdmin"):
            return HTTPResponse(body="Access denied", status=403)
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


def hash_password(password, salt):
    data_base_password = password + salt
    hashed = hashlib.md5(data_base_password.encode())
    return hashed.hexdigest()
