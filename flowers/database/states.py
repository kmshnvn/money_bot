from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from flowers.config import REDIS_PASSWORD

redis_fl = Redis(
    db=5,
    host="redis",
    port=6379,
    password=REDIS_PASSWORD,
)

storage_fl = RedisStorage(redis_fl)


class UserState(StatesGroup):
    default = State()
