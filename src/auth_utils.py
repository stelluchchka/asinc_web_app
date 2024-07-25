import jwt
from datetime import datetime, timedelta
from config import SECRET_KEY 

def generate_jwt(user_data):
    payload = {
        'user_id': user_data['id'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token
