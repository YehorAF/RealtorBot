from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from tools.text import ACTIONS


def form_btns(
    data: list[str], 
    row_btns: int, 
    callback_data: type[CallbackData],
    callback_data_list: dict[str, str | int]
) -> list[list[InlineKeyboardButton]]:
    btns = []
    row = []

    for i, d in enumerate(data):
        insert_cbd = callback_data_list | {"data": i}
        row.append(InlineKeyboardButton(
            text=d,
            callback_data=callback_data(**insert_cbd).pack()
        ))
        if (i + 1) % row_btns == 0:
            btns.append(row)
            row = []

    if row:
        btns.append(row)

    return btns


def form_move_btns(
    callback_data: type[CallbackData],
    cancel_data_list: dict[str, str | int] | None = None,
    back_data_list: dict[str, str | int] | None = None,
    next_data_list: dict[str, str | int] | None = None
) -> list[list[InlineKeyboardButton]]:
    btns = []
    moved_row = []

    if back_data_list:
        moved_row.append(InlineKeyboardButton(
            text="👈Повернутися",
            callback_data=callback_data(**back_data_list).pack()
        ))
    if next_data_list:
        moved_row.append(InlineKeyboardButton(
            text="Далі👉",
            callback_data=callback_data(**next_data_list).pack()
        ))
    if moved_row:
        btns.append(moved_row)

    if cancel_data_list:
        btns.append([InlineKeyboardButton(
            text="❌Відмінити❌",
            callback_data=callback_data(**cancel_data_list).pack()
        )])

    return btns


def form_request(data: dict[str, list | str | int]) -> str:
    action = data["action"]
    text = (
        f"Дія: {ACTIONS[action]}\n"
        f"Місто: {data.get('town')}\n"
        f"Район: {', '.join(data.get('streets') or [])}\n"
        f"Додаткова інформація про район: {data.get('street_description') or '-'}\n"
        f"Кількість кімнат: {', '.join(data.get('rooms_amount') or [])}\n"
        f"Додаткова інформація про кількість кімнат: {data.get('rooms_amount_description') or '-'}\n"
        f"Стан житла: {', '.join(data.get('appartment_condtions') or [])}\n"
        f"Опис стану житла: {data.get('appartment_condtion_description') or '-'}\n"
        f"Ціна: {data.get('price')}\n"
        f"Опис: {data.get('description')}\n"
        f"Дедлайн: {data.get('deadline') or '-'}\n"
        f"Опис дедлайну: {data.get('deadline_description') or '-'}\n"
    )

    if action == "buy":
        text += (
            f"Готовність до угоди: {data.get('agreement') or '-'}\n"
            f"Додаткова інформація до угоди: {data.get('agreement_description') or '-'}\n"
            f"Тип оплати: {data.get('payment') or '-'}\n"
            f"Додатокова інформація про оплату: {data.get('payment_description') or '-'}\n"
        )

    text += f"Контактна інформація: {data.get('telephone')}"

    return text