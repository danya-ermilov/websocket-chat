import aioredis
import json
from app.config import REDIS_URL
from datetime import datetime, timedelta


class RedisManager:
    def __init__(self) -> None:
        self.redis = None

    async def connect(self):
        if self.redis is None:
            self.redis = await aioredis.from_url(REDIS_URL)
            
    async def add_message(self, ip, username, message_data):
        data = json.loads(message_data)
        message = data['message']
        coins = data['coins']

        key = f"{ip}:{username}:{message}"

        if not await self.check_coin_limit(ip, coins):
            raise Exception("Daily coin limit exceeded")

        await self.redis.zadd('chat_messages', {key: coins})

        await self.increment_daily_coins(ip, coins)

    async def check_coin_limit(self, ip, coins):
        daily_key = f"coins:{ip}:{datetime.now().strftime('%Y-%m-%d')}"
        spent_coins = await self.redis.get(daily_key)
        spent_coins = int(spent_coins) if spent_coins else 0
        return spent_coins + coins <= 1000

    async def increment_daily_coins(self, ip, coins):
        daily_key = f"coins:{ip}:{datetime.now().strftime('%Y-%m-%d')}"
        await self.redis.incrby(daily_key, coins)
        await self.redis.expireat(daily_key, datetime.now() + timedelta(days=1))

    async def get_messages(self):
        messages = await self.redis.zrevrange('chat_messages', 0, -1, withscores=True)
        return json.dumps([
            {
                "username": msg.decode().split(':')[1],
                "message": msg.decode().split(':', 2)[2],
                "coins": int(score)
            } for msg, score in messages
        ])
    
    async def decrement_coins(self):
        all_messages = await self.redis.zrangebyscore('chat_messages', '-inf', '+inf', withscores=True)
        for message_data, coins in all_messages:
            if coins > 1:
                await self.redis.zadd('chat_messages', {message_data:coins-1})
            else:
                await self.redis.zrem('chat_messages', message_data)