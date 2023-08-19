from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis

from config_data.config import REDIS_PASSWORD

redis = Redis(
    db=3,
    host="redis",
    port=6379,
    password=REDIS_PASSWORD,
)

# storage = RedisStorage.from_url('redis://redis:6379/10')
storage = RedisStorage(redis)


class UserState(StatesGroup):
    default = State()

    # Состояние файла настроек
    settings = State()
    custom_category = State()
    custom_category_group = State()
    save_category = State()
    edit_category = State()
    rename_category = State()
    delete_category = State()

    # Состояния файла операции
    new_transaction = State()
    transaction_group = State()
    transaction_summ = State()
    transaction_category = State()
    transaction_description = State()
    transaction_new_category = State()
    start_date_transaction = State()
    save_transaction = State()
    change_transaction_details = State()
    change_transaction_details_summ = State()
    change_transaction_details_descr = State()
    change_transaction_details_category = State()

    # Состояния истории
    main_history = State()
    statistic_history = State()
    transaction_history = State()
    delete_transaction = State()
    start_date_history = State()
    end_date_history = State()
