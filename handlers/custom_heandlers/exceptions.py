from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.states import UserState
from handlers.default_heandlers.start import router


@router.message(UserState.save_transaction)
@router.message(UserState.change_transaction_details)
async def transaction_check_ex(message: Message, state: FSMContext):
    """
    Функция. Отлавливает состояние пользователя и сообщает что ожидает от него
    """
    await message.answer(
        f'Ожидаю выбор кнопки выше у сообщения. Для этого нажмите на нее'
    )


@router.message(UserState.transaction_summ)
@router.message(UserState.change_transaction_details_summ)
async def transaction_category_ex(message: Message, state: FSMContext):
    """
    Функция. Отлавливает состояние пользователя и сообщает что ожидает от него
    """
    await message.answer(
        f'🔰Ожидаю сумму операции. Нужно ввести число в формате:\n\n'
        f'🔸100\n'
        f'🔸100.00\n'
        f'🔸100,00\n',
        parse_mode='Markdown',
    )