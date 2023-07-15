from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url('redis://redis:6379/1')


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
    save_transaction = State()

    # Состояния истории
    main_history = State()
    delete_transaction = State()
