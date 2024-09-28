import asyncio
from app.redis_manager import RedisManager
from app.websocket_manager import ConnectionManager

async def start_decrement_task(redis_manager: RedisManager, manager: ConnectionManager):

    if redis_manager.redis is None:
        await redis_manager.connect()
        
    while True:
        await redis_manager.decrement_coins()
        messages = await redis_manager.get_messages()

        await manager.broadcast(messages)

        await asyncio.sleep(1)
