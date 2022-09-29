# loop.py
# Gernerate Seeds

import asyncio
import math
import csv
import aiofiles
import aiocsv

import random
import time
import uuid
import datetime

from app import db

async def growth_func(ms):
    r = 0.00007 # 0.00006
    return math.floor(100 * math.pow(math.e, r * ms))



class BackgroundRunner:
    def __init__(self):
        self.i = 0
        self.stop = False
        self.game_id = uuid.uuid4()
        self.next_game_id = uuid.uuid4()
        self.busted = True
        self.canbet = False
        self.bet_users = []
        self.queue = []
        self.history = []

    async def run_main(self, sio):
        print("[INIT] Starting...")
        start_number = random.randint(100, 1000)

        async with aiofiles.open("p.csv", mode="r") as afp:
            async for row in aiocsv.AsyncReader(afp, delimiter=","):
                self.queue.append(int(float(row[2]) * 100))
                # print(row)

        print("[INIT] Done!")

        multiplier = 500

        self.game_id = uuid.uuid4()
        self.next_game_id = uuid.uuid4()

        while True:
            # Reset Temp Info
            self.stop = False
            
            await sio.emit("future", self.queue[start_number:start_number+5])
            multiplier = self.queue.pop(start_number)
            
            # Broadcast New Game Information
            
            await sio.emit("game_id", self.game_id.__str__())
            game_start_time = int(time.time() * 1000) + 5000
            # await sio.emit("game", f"Game {self.game_id.__str__()[-6:]} will start at {game_start_time}")
            await sio.emit("time_announce", game_start_time)
            # await sio.emit("game_id", self.game_id.__str__())
            await sio.emit("final_betters", self.bet_users)
            
            his = self.history[-5:]
            his.reverse()
            await sio.emit("history", his)
            
            # Enable Betting and wait 5 Seconds
            self.bet_users = []
            self.canbet = True
            await asyncio.sleep(4.9)

            while True:
                if int(time.time() * 1000) > game_start_time:
                    break 
                await asyncio.sleep(0.15)

            # Start Game
            print("베팅 유저: ", self.bet_users)
            await sio.emit("game", f"Game {self.game_id.__str__()[-6:]} started!")
            
            
            self.canbet = False
            self.busted = False
            
            # Increase Number
            self.i = 100
            while (self.i < multiplier and self.stop == False):
                await sio.emit("score", f"{self.i}")
                elapsed = int(time.time() * 1000) - game_start_time
                self.i = await growth_func(elapsed)
                # print(f"{self.i:.2f}")
                await asyncio.sleep(0.3)

            # Crash Game & Wait 3 Seconds
            self.busted = True
            busted_score = multiplier if self.stop == False else self.i 
            await sio.emit("score", f"{busted_score}")
            await sio.emit("busted", f"{busted_score}")
            await sio.emit("game", f"Game {self.game_id.__str__()[-6:]} Busted @ {busted_score/100:.2f}x\n" + '-' * 80)

            # 전몰자 처리
            # print(self.bet_users)
            for user in self.bet_users:
                # print(user)
                # print(float(user[2]), float(busted_score/100))
                if float(user[2]) <= float(busted_score/100):
                    await db.charge_money(user[0], float(user[1]) * float(user[2]))

                    u = await db.get_user_info(user[0])

                    await sio.emit("update_user", {
                        "username": str(user[0]),
                        "balance": u["balance"]
                    })
                


            self.game_id = self.next_game_id
            self.next_game_id = uuid.uuid4()
            
            await sio.emit("next_game_id", self.next_game_id.__str__())

            self.history.append(busted_score)
            await asyncio.sleep(5)



    async def stop_now(self):
        self.stop = True
        return

    async def bet(self, sid, msg, sio):
        print(f"bet {sid} {msg}")
        # if self.canbet == True:
        if self.next_game_id.__str__() == msg["game_id"]:
            is_in_better = False
            for better in self.bet_users:
                if int(better[0]) == int(msg["username"]):
                    is_in_better = True
                    break

            if is_in_better == False:
                self.bet_users.append((str(msg["username"]), float(msg["amount"]), float(msg["cashout"])))
                # print(self.bet_users)

                await sio.emit("add_better", [
                    str(msg["username"]),
                    msg["amount"],
                    msg["cashout"]
                ])

                await db.charge_money(int(msg["username"]), -1 * int(msg["amount"]))

            user = await db.get_user_info(int(msg["username"]))

            await sio.emit("update_user", {
                "username": str(msg["username"]),
                "balance": user["balance"]
            })
        else:
            print("!! 게임 아이디 불일치 !!")
        # else:
        #     print("!! 게임 아이디 불일치 !!")
            

    async def cashout(self, user):
        in_user = False
        if self.busted == False:
            for u in self.bet_users:
                if u == user:
                    in_user = True
                    break

            if in_user:
                # 백그라운드 캐쉬아웃 DB 코드
                pass


