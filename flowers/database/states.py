from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from flowers.config import REDIS_PASSWORD, REDIS_HOST, REDIS_PORT, REDIS_DB_FL

redis_fl = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB_FL,
    password=REDIS_PASSWORD,
)

storage_fl = RedisStorage(redis_fl)


class UserState(StatesGroup):
    default = State()
