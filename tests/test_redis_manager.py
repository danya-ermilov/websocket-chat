import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.redis_manager import RedisManager

@pytest.fixture
async def redis_manager():
    redis_manager = RedisManager()
    await redis_manager.connect()  # Подключаем Redis
    yield redis_manager
    await redis_manager.redis.flushall()  # Очищаем Redis после каждого теста

@pytest.mark.asyncio
async def test_add_message(redis_manager):
    # Добавляем тестовое сообщение
    ip = "127.0.0.1"
    message_data = '{"message": "Hello, World!", "coins": 10}'
    
    await redis_manager.add_message(ip, message_data)
    
    # Проверяем, что сообщение добавлено в Redis
    messages = await redis_manager.get_messages()
    assert '{"message": "Hello, World!", "coins": 10}' in messages

@pytest.mark.asyncio
async def test_decrement_coins(redis_manager):
    # Добавляем несколько сообщений
    ip = "127.0.0.1"
    await redis_manager.add_message(ip, '{"message": "Test1", "coins": 5}')
    await redis_manager.add_message(ip, '{"message": "Test2", "coins": 3}')
    
    # Уменьшаем количество монет
    await redis_manager.decrement_coins()

    # Проверяем, что количество монет уменьшилось
    messages = await redis_manager.get_messages()
    assert '{"message": "Test1", "coins": 4}' in messages
    assert '{"message": "Test2", "coins": 2}' in messages
