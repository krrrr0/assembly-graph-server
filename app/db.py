import motor.motor_asyncio

client = motor.motor_asyncio.AsyncIOMotorClient()
db = client.assgraph


async def create_user(stu_num: int, stu_name: str, balance: float, money_spent: int, password: str):
    doc = {
        "stu_num": int(stu_num),
        "stu_name": str(stu_name),
        "password": str(password),
        "balance": float(balance),        # AST 잔액
        "money_spent": int(money_spent)   # 총 충전 KRW

    }
    result = await db.users.insert_one(doc)
    return result


async def charge_money(stu_num, amount, moneydelta=0):
    result = await db.users.find_one({'stu_num': int(stu_num)})
    if result:
        # Charge
        await db.users.find_one_and_update({'stu_num': int(stu_num)}, {'$inc': {'balance': float(amount), 'money_spent': int(moneydelta)}})
        result = await db.users.find_one({'stu_num': int(stu_num)})
        return result
    else:
        return False


async def get_user_info(stu_num, password=None):
    if password:
        result = await db.users.find_one({'stu_num': int(stu_num), 'password': str(password)})
    else:
        result = await db.users.find_one({'stu_num': int(stu_num)})
    return result


if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(create_user(21111, "오서준", 3000, 20000, "gay")))