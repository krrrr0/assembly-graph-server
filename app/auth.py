async def authenticate_user(env):
    # print(env)
    return "halcas"


import jwt
import time


# TODO
secret = 'YOUR_SECRET_HERE!'

def issue_jwt(username: str, nickname):
    data = {
        "sub": username,
        "name": nickname,
        "date": int(time.time())
    }

    token = jwt.encode(
        payload=data,
        key=secret
    )

    return token


def validate_jwt(token: str):
    try:
        result = jwt.decode(token, key=secret, algorithms=['HS256'])
    except (jwt.InvalidSignatureError, jwt.DecodeError):
        return None
    return {
        'username': result['sub'],
        'stu_name': result['name'],
        'issued': result['date']
    }


# 테스트
if __name__ == '__main__':
    print(issue_jwt('senpai', '센파이'))