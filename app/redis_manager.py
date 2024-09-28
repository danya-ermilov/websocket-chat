import aioredis
import json
from app.config import REDIS_URL

class RedisManager:
    def __init__(self) -> None:
        self.redis = None

    async def connect(self):
        if self.redis is None:
            self.redis = await aioredis.from_url(REDIS_URL)
            
    async def add_message(self, ip, message_data):
        data = json.loads(message_data)
        message = data['message']
        coins = data['coins']

        key = f"{ip}:{message}"
        await self.redis.zadd('chat_messages', {key:coins})

    async def get_messages(self):
        messages = await self.redis.zrevrange('chat_messages', 0, -1, withscores=True)
        return json.dumps([{"message": msg.decode().split(':', 1)[1], "coins": int(score)} for msg, score in messages])
    
    async def decrement_coins(self):
        all_messages = await self.redis.zrangebyscore('chat_messages', '-inf', '+inf', withscores=True)
        for message_data, coins in all_messages:
            if coins > 1:
                await self.redis.zadd('chat_messages', {message_data:coins-1})
            else:
                await self.redis.zrem('chat_messages', message_data)