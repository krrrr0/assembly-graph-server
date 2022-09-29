# main.py

import asyncio
import uvicorn
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware

import socketio

from app import worker, auth, db 
from config import __version__



sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    username: int
    password: Optional[str]
    stu_name: Optional[str]
    balance: Optional[float]
    money_spent: Optional[int]



@app.get("/test")
async def test():
    return {
        "version": __version__
    }

# User Information
@app.post("/login")
async def login(user: User, response: Response):
    # 보안은 개나 준다
    username = user.username #.lower()
    password = user.password

    # DB 쿼리 여기에

    q = await db.get_user_info(username, password)

    if not q:
        return {
            "result": "error",
            "msg": "아이디나 패스워드가 올바르지 않습니다."
        }
    
    jwt = auth.issue_jwt(username, q['stu_name'])
    response.set_cookie(key="jwt", value=jwt, samesite="none", httponly=True)
        

    return {
        "result": "success",
        'data': {
            'token': jwt
        }
    }

# User Information
@app.get("/user")
async def get_user_info(username: str):

    print(username)
    # 보안은 개나 준다

    result = await db.get_user_info(username)

    if result:
        return {
            "result": "success",
            "user": {
                "stu_num": int(result['stu_num']),
                "stu_name": result['stu_name'],
                "balance": float(result['balance']),        # AST 잔액
                "money_spent": int(result['money_spent'])   # 총 충전 KRW
            }
        }
    else:
        return {
            "result": "error",
            "msg": "사용자 정보를 조회할 수 없습니다. 직원에게 문의해 주세요."
        }

@app.post("/user")
async def create_modify_user(user: User):
    if await db.get_user_info(int(user.username)):
        # 사용자가 이미 있을 경우
        await db.charge_money(int(user.username), float(user.balance), int(user.money_spent))
        return {
            "result": "success",
            "msg": "이미 있는 사용자로 충전을 진행하였습니다. 비밀번호는 바뀌지 않았습니다."
        }

    await db.create_user(int(user.username), user.stu_name, float(user.balance), int(user.money_spent), user.password)
    return {
        "result": "success",
        "msg": "성공적으로 계정을 생성하고 충전하였습니다."
    }




runner = worker.BackgroundRunner()

@app.on_event('startup')
async def app_startup():
    asyncio.create_task(runner.run_main(sio))



app.mount("/", socket_app)
# app.add_route("/socket.io/", route=socket_app, methods=['GET', 'POST'])
# app.add_websocket_route("/socket.io/", socket_app)


@sio.on("connect")
async def connect(sid, env):
    username = await auth.authenticate_user(env)
    await sio.save_session(sid, {'username': username})

    print("on connect")


@sio.on("direct")
async def direct(sid, msg):
    print(f"direct {msg}")
    await sio.emit("event_name", msg, room=sid)  # we can send message to specific sid

@sio.on("chat")
async def chat(sid, msg):
    session = await sio.get_session(sid)
    print(f"[{session['username']}]", msg)
    await sio.emit("chat", msg)     # Broadcast Chatting

@sio.on("broadcast")
async def broadcast(sid, msg):
    print(f"broadcast {msg}")
    await sio.emit("event_name", msg)  # or send to everyone

@sio.on("bet")
async def place_bet(sid, msg):
    await runner.bet(sid, msg, sio)

# 테스트용
# @sio.on("break")
# async def abort(sid, msg):
#     print("!!! [BREAK] !!!")
#     await runner.stop_now()


@sio.on("disconnect")
async def disconnect(sid):
    print("on disconnect")


if __name__ == "__main__":
    kwargs = {"host": "0.0.0.0", "port": 5000, "workers": 20}
    kwargs.update({"debug": True, "reload": True})
    uvicorn.run("main:app", **kwargs)