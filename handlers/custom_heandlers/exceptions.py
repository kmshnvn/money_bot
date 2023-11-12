from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.states import UserState
from handlers.default_heandlers.start import router


@router.message(UserState.save_transaction)
@router.message(UserState.change_transaction_details)
@router.message(UserState.choose_category_for_change)
@router.message(UserState.settings)
@router.message(UserState.custom_category_group)
@router.message(UserState.save_category)
@router.message(UserState.delete_category)
@router.message(UserState.rename_category)
async def transaction_check_ex(message: Message, state: FSMContext):
    """
    Функция. Отлавливает состояние пользователя и сообщает что ожидает от него
    """
    await message.answer(
        f"Ожидаю выбор кнопки выше у сообщения. Для этого нажмите на нее"
    )


@router.message(UserState.transaction_summ)
@router.message(UserState.change_transaction_details_summ)
async def transaction_category_ex(message: Message, state: FSMContext):
    """
    Функция. Отлавливает состояние пользователя и сообщает что ожидает от него
    """
    await message.answer(
        f"🔰Ожидаю сумму операции. Нужно ввести число в формате:\n\n"
        f"🔸100\n"
        f"🔸100.0\n"
        f"🔸100,0\n"
        f"🔸100.00\n"
        f"🔸100,00\n\n"
        f"Также можно ввести сумму для калькулятора в формате:\n"
        f"🔹100+100,0+..",
    )


@router.callback_query(Text(startswith="change_success_transaction"))
async def transaction_category_ex(callback: CallbackQuery, state: FSMContext):
    """
    Функция. Отлавливает кнопку от пользователя и дает ему инстуркцию, что нужно сделать
    """
    await callback.message.answer(
        f"Чтобы изменить операцию нужно нажать на '🧮Новая операция', "
        f"либо нажмите /transaction\n\n"
        f"После этого нажмите на кнопку повторно"
    )
