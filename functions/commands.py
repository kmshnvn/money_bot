from datetime import date

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from database.database import db_get_transaction, db_get_category
from database.states import UserState
from keyboards.inline_keyboards import (
    delete_history_kb,
    change_success_transaction_details_kb,
)


async def check_delete_transaction(
    message: Message, state: FSMContext, split_text: str
) -> None:
    """
    Обработчик команды удаления операции из истории (не callback).
    """
    try:
        logger.info(
            f"{message.chat.id} - Уточняем удаление операции с переходом из истории"
        )

        transaction_id = int(split_text[3:])
        transaction = db_get_transaction(transaction_id, message.chat.id)

        if transaction:
            amount = float(transaction.get("amount"))
            summ = amount if amount >= 0 else -amount
            transaction_date = date.strftime(
                transaction["transaction_date"], "%d.%m.%Y"
            )

            await state.set_data(
                {
                    "delete_transaction": {
                        "id": transaction_id,
                        "user_id": message.chat.id,
                        "summ": amount,
                    },
                    "transaction_info": {
                        "transaction_date": transaction_date,
                        "category_name": transaction.get("category_name"),
                        "summ": summ,
                        "description": transaction.get("description"),
                    },
                }
            )

            text = (
                f"Выбрана операция\n\n"
                f"*Дата операции: {transaction_date}*\n"
                f'{summ} ₽ в категории {transaction["category_name"]}\n'
                f'Описание: {transaction["description"]}\n\n'
                f"Удаляем операцию?"
            )

            await message.answer(f"{text}", reply_markup=delete_history_kb())
        else:
            await message.answer(
                text="Операция уже удалена или не существует",
            )

    except Exception as ex:
        logger.error(f"Что-то пошло не так при уточнении удаления операции: {ex}")
        await message.answer(
            "🤕 Возникла ошибка при уточнении удаления операции. Скоро меня починят"
        )


async def change_transaction_from_history(
    message: Message, state: FSMContext, split_text: str
):
    """
    Обработчик команды изменения операции из истории (не callback).
    """
    logger.info(
        f"{message.chat.id} - Уточняем изменение операции с переходом из истории"
    )

    transaction_id = int(split_text[6:])
    transaction = db_get_transaction(int(transaction_id), message.chat.id)

    if transaction:
        amount = float(transaction.get("amount"))
        summ = amount if amount >= 0 else -amount
        group = "Income" if amount >= 0 else "Expense"
        transaction_date = date.strftime(transaction["transaction_date"], "%d.%m.%Y")

        user_category = db_get_category(tg_id=message.chat.id)

        await state.update_data(
            {
                "id": transaction_id,
                "change_summ": "",
                "change_descr": "",
                "change_date": "",
                "change_category": "",
                "old_transaction_info": {
                    "old_date": transaction_date,
                    "old_summ": float(transaction["amount"]),
                    "old_category": transaction["category_name"],
                    "old_descr": transaction["description"],
                    "old_group": group,
                },
            },
        )
        await state.update_data(user_category)

        text = (
            f"Выбрана операция\n\n"
            f"*Дата операции: {transaction_date}*\n"
            f'{summ} ₽ в категории {transaction["category_name"]}\n'
            f'Описание: {transaction["description"]}\n\n'
        )
        await state.set_state(UserState.change_success_transaction_details)

        await message.answer(
            text=f"{text}Что будем менять?",
            reply_markup=change_success_transaction_details_kb(),
        )
    else:
        await message.answer(
            text=f"Операция уже удалена или не существует",
        )
