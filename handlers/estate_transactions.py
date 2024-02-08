import asyncio
from datetime import datetime
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton,\
    InlineKeyboardMarkup

from tools.callbacks import ReqOrderCallback, StateCallback
from tools.database import Database
from tools.formatter import form_btns, form_move_btns, form_request
from tools.keyboard import go_to_start_ikb
from tools.text import TOWNS, STREETS, ROOMS, CONDITIONS, DEADLINES, ACTIONS,\
    AGREEMENTS, PAYMENTS, SEND_ORDERS_TO
from tools.states import EstateTransactionStates


estate_transactions_router = Router()


# cancel


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "cancel_ref")
)
async def cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        text=(
            "Реєстрацію було відмінено. "
            "Натисніть повернутися, щоб перейти на початкове вікно"
        ),
        reply_markup=go_to_start_ikb
    )


# select town actions


@estate_transactions_router.callback_query(
    StateCallback.filter((F.msg == "select_town") & (
        (F.data == "create_ref") | (F.data == "back")))
)
async def select_town(
    callback: CallbackQuery, 
    callback_data: StateCallback, 
    state: FSMContext
):
    action = callback_data.action
    data = callback_data.data
    msg_id = callback.message.message_id

    await state.set_state(EstateTransactionStates.town)
    await state.update_data({"msg_id": msg_id})

    btns = form_btns(
        data=TOWNS, 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_town", "msg": "choose_town"
        }
    )

    if data == "create_ref":
        await state.update_data({"action": action})
    else:
        storage_data = await state.get_data()
        town = storage_data.get("town")

        for row in btns:
            for btn in row:
                if btn.text == town:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        next_data_list={
            "action": "next", "msg": "select_street", "data": "next"
        }
    )
    rent_or_buy = "орендувати" if action == "rent" else "придбати"

    await callback.message.edit_text(
        text=f"В якому місті ви хочете {rent_or_buy} житло? 🇺🇦",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "choose_town"),
    EstateTransactionStates.town
)
async def choose_town(
    callback: CallbackQuery, callback_data: StateCallback, state: FSMContext
):
    ind = int(callback_data.data)
    town = TOWNS[ind]
    st_town = (await state.get_data()).get("town")

    if town == st_town:
        town = ""

    await state.update_data({"town": town})

    btns = form_btns(
        data=TOWNS, 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_town", "msg": "choose_town"
        }
    )

    for row in btns:
        for btn in row:
            if btn.text == town:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        next_data_list={
            "action": "next", "msg": "select_street", "data": "next"
        }
    )

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))


# select street actions


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "select_street"), 
    # EstateTransactionStates.town,
    # EstateTransactionStates.rooms_amount
)
async def select_streets(
    callback: CallbackQuery, state: FSMContext
):
    await state.set_state(EstateTransactionStates.street)
    storage_data = await state.get_data()
    town = storage_data.get("town")

    if not town:
        await callback.answer(
            text=("Вам необхідно обрати місто, "
                    "щоб продовжити заповнювати форму далі"),
            show_alert=True
        )
        await state.set_state(EstateTransactionStates.town)
        return

    btns = form_btns(
        data=STREETS[town], 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_street", "msg":"choose_street"
        }
    )
    streets = storage_data.get("streets")

    if streets:
        for row in btns:
            for btn in row:
                if btn.text in streets:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_town", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "select_rooms_amount", "data": "next"
        }
    )
    street_description = storage_data.get("street_description") or ""

    if street_description:
        street_description = f"\n\nДодаткова інформація: {street_description}"

    await callback.message.edit_text(
        text=(
            "Які райони готові роздивитись?🏘"
            f"(оберіть або напишіть свій варіант){street_description}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.message(
    EstateTransactionStates.street
)
async def insert_street_description(
    message: Message, state: FSMContext
):
    text = message.text
    storage_data = await state.get_data()
    msg_id = storage_data["msg_id"]
    town = storage_data["town"]
    streets = storage_data.get("streets") or []

    btns = form_btns(
        data=STREETS[town], 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_street", "msg":"choose_street"
        }
    )

    if streets:
        for row in btns:
            for btn in row:
                if btn.text in streets:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_town", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "select_rooms_amount", "data": "next"
        }
    )

    await state.update_data({"street_description": text})
    await message.bot.edit_message_text(
        text=("Які райони готові роздивитись?🏘 "
              "(оберіть або напишіть свій варіант)"
              f"\n\nДодаткова інформація: {text}"),
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "choose_street"),
    EstateTransactionStates.street
)
async def choose_street(
    callback: CallbackQuery,
    callback_data: StateCallback, 
    state: FSMContext
):
    ind = int(callback_data.data)
    storage_data = await state.get_data()
    town = storage_data["town"]
    street = STREETS[town][ind]
    streets = storage_data.get("streets") or []

    if street in streets:
        i = streets.index(street)
        streets.pop(i)
    else:
        streets.append(street)

    await state.update_data({"streets": streets})

    btns = form_btns(
        data=STREETS[town], 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_street", "msg":"choose_street"
        }
    )

    if streets:
        for row in btns:
            for btn in row:
                if btn.text in streets:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_town", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "select_rooms_amount", "data": "next"
        }
    )

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


# select amount of rooms actions


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "select_rooms_amount"),
    # EstateTransactionStates.street,
    # EstateTransactionStates.condition
)
async def select_rooms_amount(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EstateTransactionStates.rooms_amount)
    storage_data = await state.get_data()

    if (not storage_data.get("streets") and 
        not storage_data.get("street_description")):
        await state.set_state(EstateTransactionStates.street)
        await callback.answer(
            text=(
                "Вам необхідно обрати вулицю або "
                "написати опис ваших побажань, щоб продовжити"
            ),
            show_alert=True
        )
        return

    btns = form_btns(
        data=ROOMS,
        row_btns=2,
        callback_data=StateCallback,
        callback_data_list={
            "action": "choose_rooms_amount",
            "msg": "choose_rooms_amount"
        }
    )
    rooms_amounts = storage_data.get("rooms_amount")

    if rooms_amounts:
        for row in btns:
            for btn in row:
                if btn.text in rooms_amounts:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_street", "data": "back"
        },
        next_data_list={
            "action": "next", 
            "msg": "select_appartment_conditions", 
            "data": "next"
        }
    )

    description = storage_data.get("rooms_amount_description") or ""

    if description:
        description = f"\n\nДодаткова інформація: {description}"

    await callback.message.edit_text(
        text=(
            "Кількість кімнат які готові роздивитись?👨‍👩‍👧‍👦 "
            f"(оберіть або напишіть свій варіант){description}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.message(EstateTransactionStates.rooms_amount)
async def insert_rooms_amount_description(
    message: Message, state: FSMContext
):
    text = message.text
    storage_data = await state.get_data()
    msg_id = storage_data["msg_id"]
    rooms_amounts = storage_data.get("rooms_amount") or []

    btns = form_btns(
        data=ROOMS, 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_rooms_amount", "msg": "choose_rooms_amount"
        }
    )

    if rooms_amounts:
        for row in btns:
            for btn in row:
                if btn.text in rooms_amounts:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_street", "data": "back"
        },
        next_data_list={
            "action": "next", 
            "msg": "select_appartment_conditions", 
            "data": "next"
        }
    )

    await state.update_data({"rooms_amount_description": text})
    await message.bot.edit_message_text(
        text=("Кількість кімнат які готові роздивитись?👨‍👩‍👧‍👦 "
              "(оберіть або напишіть свій варіант)"
              f"\n\nДодаткова інформація: {text}"),
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "choose_rooms_amount"),
    EstateTransactionStates.rooms_amount
)
async def choose_rooms_amount(
    callback: CallbackQuery,
    callback_data: StateCallback,
    state: FSMContext
):
    ind = int(callback_data.data)
    rooms_amount = ROOMS[ind]
    storage_data = await state.get_data()
    rooms_amounts = storage_data.get("rooms_amount") or []

    if rooms_amount in rooms_amounts:
        i = rooms_amounts.index(rooms_amount)
        rooms_amounts.pop(i)
    else:
        rooms_amounts.append(rooms_amount)

    await state.update_data({"rooms_amount": rooms_amounts})

    btns = form_btns(
        data=ROOMS, 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_rooms_amount", "msg": "choose_rooms_amount"
        }
    )

    if rooms_amounts:
        for row in btns:
            for btn in row:
                if btn.text in rooms_amounts:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_street", "data": "back"
        },
        next_data_list={
            "action": "next", 
            "msg": "select_appartment_conditions", 
            "data": "next"
        }
    )

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


# select appartment conditions actions


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "select_appartment_conditions"),
    # EstateTransactionStates.rooms_amount,
    # EstateTransactionStates.price
)
async def select_appartment_conditions(
    callback: CallbackQuery, state: FSMContext
):
    await state.set_state(EstateTransactionStates.condition)
    storage_data = await state.get_data()

    if (not storage_data.get("rooms_amount") and 
        not storage_data.get("rooms_amount_description")):
        await state.set_state(EstateTransactionStates.rooms_amount)
        await callback.answer(
            text=(
                "Вам необхідно обрати кількість кімнат або "
                "написати опис ваших побажань, щоб продовжити"
            ),
            show_alert=True
        )
        return
    
    action = storage_data["action"]
    btns = form_btns(
        data=CONDITIONS[action], 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_condition", "msg":"choose_appartment_condition"
        }
    )

    appartment_conditions = storage_data.get("appartment_condtions")
    print(appartment_conditions)

    if appartment_conditions:
        for row in btns:
            for btn in row:
                if btn.text in appartment_conditions:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_rooms_amount", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "set_price", "data": "next"
        }
    )

    description = storage_data.get("appartment_condition_description") or ""
    
    if description:
        description = f"\n\nДодаткова інформація: {description}"

    await callback.message.edit_text(
        text=(
            "В якому стані більш притаманно?🔨 "
            f"(оберіть або напишіть свій варіант){description}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.message(EstateTransactionStates.condition)
async def add_appartment_condition(message: Message, state: FSMContext):
    text = message.text
    storage_data = await state.get_data()
    msg_id = storage_data["msg_id"]
    appartment_conditions = storage_data.get("appartment_condtions") or []
    action = storage_data["action"]

    btns = form_btns(
        data=CONDITIONS[action], 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_appartment_condition", 
            "msg": "choose_appartment_condition"
        }
    )

    if appartment_conditions:
        for row in btns:
            for btn in row:
                if btn.text in appartment_conditions:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", 
            "msg": "select_rooms_amount", 
            "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "set_price", "data": "next"
        }
    )

    await state.update_data({"appartment_condition_description": text})
    await message.bot.edit_message_text(
        text=("В якому стані більш притаманно?🔨 "
              "(оберіть або напишіть свій варіант)"
              f"\n\nДодаткова інформація: {text}"),
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "choose_appartment_condition"),
    EstateTransactionStates.condition
)
async def choose_appartment_condition(
    callback: CallbackQuery, callback_data: StateCallback, state: FSMContext
):
    ind = int(callback_data.data)
    storage_data = await state.get_data()
    action = storage_data["action"]
    condition = CONDITIONS[action][ind]
    appartment_conditions = storage_data.get("appartment_condtions") or []

    if condition in appartment_conditions:
        i = appartment_conditions.index(condition)
        appartment_conditions.pop(i)
    else:
        appartment_conditions.append(condition)

    await state.update_data({"appartment_condtions": appartment_conditions})

    btns = form_btns(
        data=CONDITIONS[action], 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_appartment_condition", 
            "msg": "choose_appartment_condition"
        }
    )

    if appartment_conditions:
        for row in btns:
            for btn in row:
                if btn.text in appartment_conditions:
                    btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", 
            "msg": "select_rooms_amount", 
            "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "set_price", "data": "next"
        }
    )

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


# set price action


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "set_price"),
    # EstateTransactionStates.condition,
    # EstateTransactionStates.description
)
async def set_price_msg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EstateTransactionStates.price)
    storage_data = await state.get_data()

    if (not storage_data.get("appartment_condtions") and 
        not storage_data.get("appartment_condition_description")):
        await state.set_state(EstateTransactionStates.condition)
        await callback.answer(
            text=(
                "Вам необхідно обрати стан житла або "
                "написати опис ваших побажань, щоб продовжити"
            ),
            show_alert=True
        )
        return

    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", 
            "msg": "select_appartment_conditions", 
            "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "set_description", "data": "next"
        }
    )
    price = storage_data.get("price") or ""

    if price:
        price = f"\n\nСума: {price}"

    action = storage_data["action"]
    currency = "грн" if action == "rent" else "$"

    await callback.message.edit_text(
        text=f"До якої суми готові роздивитись?💰 (напишіть в {currency}){price}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.message(
    EstateTransactionStates.price
)
async def set_price(message: Message, state: FSMContext):
    price = message.text

    await state.update_data({"price": price})
    storage_data = await state.get_data()
    msg_id = storage_data["msg_id"]

    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", 
            "msg": "select_appartment_conditions", 
            "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "set_description", "data": "next"
        }
    )

    action = storage_data["action"]
    currency = "грн" if action == "rent" else "$"

    await message.bot.edit_message_text(
        text=(
            f"До якої суми готові роздивитись?💰 (напишіть в {currency})"
            f"\n\nСума: {price}"
        ),
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


# set description action


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "set_description"),
    # EstateTransactionStates.price,
    # EstateTransactionStates.deadline
)
async def set_description_msg(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EstateTransactionStates.description)
    storage_data = await state.get_data()

    if not storage_data.get("price"):
        await state.set_state(EstateTransactionStates.price)
        await callback.answer(
            text="Вам необхідно ввести бажану суму",
            show_alert=True
        )
        return

    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "set_price", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "select_deadline", "data": "next"
        }
    )
    description = storage_data.get("description") or ""

    if description:
        description = f"\n\nОпис: {description}"

    await callback.message.edit_text(
        text=(
            "Що для Вас ще буде важливим при виборі "
            f"квартири вашої мрії?👑 (напишіть){description}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.message(EstateTransactionStates.description)
async def set_description(message: Message, state: FSMContext):
    msg_id = (await state.get_data())["msg_id"]
    description = message.text

    await state.update_data({"description": description})

    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "set_price", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "select_deadline", "data": "next"
        }
    )

    await message.bot.edit_message_text(
        text=(
            "Що для Вас ще буде важливим при виборі квартири вашої мрії?👑 (напишіть)\n\n"
            f"Опис: {description}"
        ),
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


# set deadline action


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "select_deadline"),
    # EstateTransactionStates.description,
    # EstateTransactionStates.telephone

)
async def select_deadline(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EstateTransactionStates.deadline)
    storage_data = await state.get_data()

    if not storage_data.get("description"):
        await callback.answer(
            text="Вам необхідно внести опис, щоб продовжити далі",
            show_alert=True
        )
        await state.set_state(EstateTransactionStates.description)
        return

    btns = form_btns(
        data=DEADLINES, 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_deadline", "msg": "choose_deadline"
        }
    )
    deadline = storage_data.get("deadline")

    for row in btns:
        for btn in row:
            if btn.text == deadline:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "set_description", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "set_telephone_number", "data": "next"
        }
    )
    description = storage_data.get("deadline_description") or ""

    if description:
        description = f"\n\nДодаткова інформація: {description}"

    action = storage_data["action"]
    uact = "заїхати" if action == "rent" else "придбати"

    await callback.message.edit_text(
        text=(
            f"Які у Вас терміни для того, щоб {uact}?"
            f"(оберіть або напишіть точний термін){description}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "choose_deadline"),
    EstateTransactionStates.deadline
)
async def set_callback_deadline(
    callback: CallbackQuery,
    callback_data: StateCallback,
    state: FSMContext
):
    ind = int(callback_data.data)
    deadline = DEADLINES[ind]
    st_deadline = (await state.get_data()).get("deadline")

    if deadline == st_deadline:
        deadline = ""

    await state.update_data({"deadline": deadline})

    btns = form_btns(
        data=DEADLINES, 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_deadline", "msg": "choose_deadline"
        }
    )

    for row in btns:
        for btn in row:
            if btn.text == deadline:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "set_description", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "set_telephone_number", "data": "next"
        }
    )

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.message(EstateTransactionStates.deadline)
async def set_deadline_description(message: Message, state: FSMContext):
    description = message.text

    await state.update_data({"deadline_description": description})

    storage_data = await state.get_data()
    action = storage_data["action"]
    uact = "заїхати" if action == "rent" else "придбати"
    text = (f"Які у Вас терміни для того, щоб {uact}?"
            "(оберіть або напишіть точний термін)")
    deadline = storage_data.get("deadline")
    msg_id = storage_data["msg_id"]

    btns = form_btns(
        data=DEADLINES, 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_deadline", "msg": "choose_deadline"
        }
    )

    for row in btns:
        for btn in row:
            if btn.text == deadline:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "set_description", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "set_telephone_number", "data": "next"
        }
    )

    text += f"\n\nДодаткова інформація: {description}"

    await message.bot.edit_message_text(
        text=text,
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


# telephone number actions


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "set_telephone_number"),
    # EstateTransactionStates.deadline,
    # EstateTransactionStates.check_reference
)
async def set_telephone_number_msg(
    callback: CallbackQuery, state: FSMContext
):
    await state.set_state(EstateTransactionStates.telephone)
    storage_data = await state.get_data()

    if (not storage_data.get("deadline") and
        not storage_data.get("deadline_description")):
        await state.set_state(EstateTransactionStates.deadline)
        await callback.answer(
            text="Вам необхідно внести дані про дедлайн або його опис",
            show_alert=True
        )
        return

    action = storage_data["action"]
    msg = "check_reference" if action == "rent" else "select_agreement"
    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_deadline", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": msg, "data": "next"
        }
    )
    telephone = storage_data.get("telephone") or ""

    if telephone:
        telephone = f"\n\nКонтактні дані: {telephone}"

    await callback.message.edit_text(
        text=("Чудово, з основном ми вже впорались, "
              "тепер Вам залишилось написати свій номер телефона та своє ім'я, "
              f"для того щоб я зміг з Вами зв‘язатись!{telephone}"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.message(
    EstateTransactionStates.telephone
)
async def set_telephone_number(message: Message, state: FSMContext):
    telephone = message.text

    await state.update_data({"telephone": telephone})

    storage_data = await state.get_data()
    msg_id = storage_data["msg_id"]
    action = storage_data["action"]
    msg = "check_reference" if action == "rent" else "select_agreement"

    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_deadline", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": msg, "data": "next"
        }
    )

    await message.bot.edit_message_text(
        text=("Чудово, з основном ми вже впорались, "
              "тепер Вам залишилось написати свій номер телефона та своє ім'я, "
              "для того щоб я зміг з Вами зв‘язатись!\n\n"
              f"Контактні дані: {telephone}"),
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


# select agreement actions
    

@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "select_agreement")
)
async def select_agreement(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EstateTransactionStates.agreement)
    storage_data = await state.get_data()

    if not storage_data.get("telephone"):
        await state.set_state(EstateTransactionStates.telephone)
        await callback.answer(
            text="Вам необхідно внести контактні дані, щоб продовжити далі",
            show_alert=True
        )
        return

    btns = form_btns(
        data=AGREEMENTS,
        row_btns=2,
        callback_data=StateCallback,
        callback_data_list={
            "action": "choose_agreement", "msg": "choose_agreement"
        }
    )
    agreement = storage_data.get("agreement")

    for row in btns:
        for btn in row:
            if btn.text == agreement:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "set_telephone_number", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "select_payment", "data": "next"
        }
    )
    description = storage_data.get("agreement_description") or ""

    if description:
        description = f"\n\nДодаткова інформація: {description}"

    await callback.message.edit_text(
        text=(
            "Чи готові ви до швидкої угоди, "
            "чи вам треба спочатку продати свою нерухомість? "
            f"(оберіть або напишіть додаткову інормацію){description}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "choose_agreement"),
    EstateTransactionStates.agreement
)
async def choose_agreement(
    callback: CallbackQuery, callback_data: StateCallback, state: FSMContext
):
    ind = int(callback_data.data)
    agreement = AGREEMENTS[ind]
    st_agreement = (await state.get_data()).get("agreement")

    if agreement == st_agreement:
        agreement == ""

    await state.update_data({"agreement": agreement})

    btns = form_btns(
        data=AGREEMENTS, 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_agreement", "msg": "choose_agreement"
        }
    )

    for row in btns:
        for btn in row:
            if btn.text == agreement:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "set_telephone_number", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "select_payment", "data": "next"
        }
    )

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.message(
    EstateTransactionStates.agreement
)
async def set_agreement_description(message: Message, state: FSMContext):
    description = message.text
    storage_data = await state.update_data(
        {"agreement_description": description})
    msg_id = storage_data["msg_id"]

    btns = form_btns(
        data=AGREEMENTS,
        row_btns=2,
        callback_data=StateCallback,
        callback_data_list={
            "action": "choose_agreement", "msg": "choose_agreement"
        }
    )
    agreement = storage_data.get("agreemnt")

    for row in btns:
        for btn in row:
            if btn.text == agreement:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "set_telephone_number", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "select_payment", "data": "next"
        }
    )

    await message.bot.edit_message_text(
        text=(
            "Чи готові ви до швидкої угоди, "
            "чи вам треба спочатку продати свою нерухомість? "
            "(оберіть або напишіть додаткову інормацію)\n\n"
            f"Додаткова інформація: {description}"
        ),
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


# select payment actions
    

@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "select_payment")
)
async def select_payment(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EstateTransactionStates.payment)
    storage_data = await state.get_data()

    if (not storage_data.get("agreement") and 
        storage_data.get("agreement_description")):
        await state.set_state(EstateTransactionStates.agreement)
        await callback.answer(
            text="Вам необхідно внести тип угоди або ж описати його",
            show_alert=True
        )
        return

    btns = form_btns(
        data=PAYMENTS,
        row_btns=2,
        callback_data=StateCallback,
        callback_data_list={
            "action": "choose_payment", "msg": "choose_payment"
        }
    )
    payment = storage_data.get("payment")

    for row in btns:
        for btn in row:
            if btn.text == payment:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_agreement", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "check_reference", "data": "next"
        }
    )
    description = storage_data.get("payment_description") or ""

    if description:
        description = f"\n\nДодаткова інформація: {description}"

    await callback.message.edit_text(
        text=(
            "Яким чином вам буде зручніше всього розраховуватись? "
            f"(Оберіть або напишіть свій варіант){description}"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "choose_payment")
)
async def choose_payment(
    callback: CallbackQuery, callback_data: StateCallback, state: FSMContext
):
    ind = int(callback_data.data)
    payment = PAYMENTS[ind]
    st_payment = (await state.get_data()).get("payment")

    print(payment, st_payment, payment == st_payment)

    if payment == st_payment:
        payment = ""

    print(payment, st_payment, payment == st_payment)

    await state.update_data({"payment": payment})

    btns = form_btns(
        data=PAYMENTS, 
        row_btns=2, 
        callback_data=StateCallback, 
        callback_data_list={
            "action": "choose_payment", "msg": "choose_payment"
        }
    )

    for row in btns:
        for btn in row:
            if btn.text == payment:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_agreement", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "check_reference", "data": "next"
        }
    )

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@estate_transactions_router.message(
    EstateTransactionStates.payment
)
async def set_agreement_description(message: Message, state: FSMContext):
    description = message.text
    storage_data = await state.update_data(
        {"payment_description": description})
    msg_id = storage_data["msg_id"]

    btns = form_btns(
        data=PAYMENTS,
        row_btns=2,
        callback_data=StateCallback,
        callback_data_list={
            "action": "choose_payment", "msg": "choose_payment"
        }
    )
    payment = storage_data.get("payment")

    for row in btns:
        for btn in row:
            if btn.text == payment:
                btn.text = "✅" + btn.text

    btns += form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "select_agreement", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "check_reference", "data": "next"
        }
    )

    await message.bot.edit_message_text(
        text=(
            "Яким чином вам буде зручніше всього розраховуватись? "
            "(Оберіть або напишіть свій варіант)\n\n"
            f"Додаткова інформація: {description}"
        ),
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


# check reference action


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "check_reference"),
    # EstateTransactionStates.telephone
)
async def check_callback_reference(
    callback: CallbackQuery, state: FSMContext
):
    await state.set_state(EstateTransactionStates.check_reference)
    data = await state.get_data()

    if (not data.get("telephone") and data.get("action") == "rent"):
        await state.set_state(EstateTransactionStates.telephone)
        await callback.answer(
            text="Вам необхідно внести контактні дані, щоб продовжити далі",
            show_alert=True
        )
        return
    elif (not data.get("payment_description") and
          not data.get("payment") and 
          data.get("action") == "buy"):
        await state.set_state(EstateTransactionStates.payment)
        await callback.answer(
            text="Вам необхідно внести тип оплати або його опис, щоб продовжити",
            show_alert=True
        )
        return

    text = form_request(data)
    text = "Перевірте запит\n\n" + text 
    # text = (
    #     "Перевірте запит\n\n"
    #     f"Дія: {ACTIONS[data.get('action')]}\n"
    #     f"Місто: {data.get('town')}\n"
    #     f"Район: {', '.join(data.get('streets') or [])}\n"
    #     f"Додаткова інформація про район: {data.get('street_description') or '-'}\n"
    #     f"Кількість кімнат: {', '.join(data.get('rooms_amount') or [])}\n"
    #     f"Додаткова інформація про кількість кімнат: {data.get('rooms_amount_description') or '-'}\n"
    #     f"Стан житла: {', '.join(data.get('appartment_condtions') or [])}\n"
    #     f"Опис стану житла: {data.get('appartment_condtion_description') or '-'}\n"
    #     f"Ціна: {data.get('price')}\n"
    #     f"Опис: {data.get('description')}\n"
    #     f"Дедлайн: {data.get('deadline') or '-'}\n"
    #     f"Опис дедлайну: {data.get('deadline_description') or '-'}\n"
    #     f"Контактна інформація: {data.get('telephone')}"
    # )
    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", "msg": "cancel_ref", "data": "cancel"
        },
        back_data_list={
            "action": "back", "msg": "set_telephone_number", "data": "back"
        },
        next_data_list={
            "action": "next", "msg": "send_reference", "data": "next"
        }
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


# send reference action


@estate_transactions_router.callback_query(
    StateCallback.filter(F.msg == "send_reference"),
    EstateTransactionStates.check_reference
)
async def send_reference(
    callback: CallbackQuery, state: FSMContext, db: Database
):
    data = await state.get_data()
    await state.clear()

    await callback.message.edit_text(
        text="Дякуємо за запит! Найближчим часом з вами зв'яжуться 😉",
        reply_markup=go_to_start_ikb
    )

    customer_tg_id = callback.from_user.id
    text = form_request(data)
    text = (
        "Запит на надання кваліфікованої допомоги\n"
        f"Користувач: <a href=\"tg://user?id={customer_tg_id}\">{customer_tg_id}</a>\n\n"
    ) + text
    # text = (
    #     "Запит на надання кваліфікованої допомоги\n"
    #     f"Користувач: <a href=\"tg://user?id={customer_tg_id}\">{customer_tg_id}</a>\n\n"
    #     f"Дія: {ACTIONS[data.get('action')]}\n"
    #     f"Місто: {data.get('town')}\n"
    #     f"Район: {', '.join(data.get('streets') or [])}\n"
    #     f"Додаткова інформація про район: {data.get('street_description') or '-'}\n"
    #     f"Кількість кімнат: {', '.join(data.get('rooms_amount') or [])}\n"
    #     f"Додаткова інформація про кількість кімнат: {data.get('rooms_amount_description') or '-'}\n"
    #     f"Стан житла: {', '.join(data.get('appartment_condtions') or [])}\n"
    #     f"Опис стану житла: {data.get('appartment_condtion_description') or '-'}\n"
    #     f"Ціна: {data.get('price')}\n"
    #     f"Опис: {data.get('description')}\n"
    #     f"Дедлайн: {data.get('deadline') or '-'}\n"
    #     f"Опис дедлайну: {data.get('deadline_description') or '-'}\n"
    #     f"Контактна інформація: {data.get('telephone')}"
    # )
    dt = datetime.now().strftime("%d.%m.%Y-%H:%M:%S")

    result = await db.orders.add_one({
        "customer_tg_id": customer_tg_id,
        "ordered_time": dt,
        "text": text,
        "status": "process"
    })
    order_id = str(result.inserted_id)

    try:
        await callback.bot.send_message(
            chat_id=SEND_ORDERS_TO,
            text=text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Взятися",
                        callback_data=ReqOrderCallback(
                            action="get_job", 
                            user_id=customer_tg_id, 
                            order_id=order_id
                        ).pack()
                    ),
                    InlineKeyboardButton(
                        text="Відхилити",
                        callback_data=ReqOrderCallback(
                            action="reject_job", 
                            user_id=customer_tg_id,
                            order_id=order_id
                        ).pack()
                    )
                ], [
                    InlineKeyboardButton(
                        text="Заблокувати користувача",
                        callback_data=ReqOrderCallback(
                            action="ban_user", 
                            user_id=customer_tg_id,
                            order_id=order_id
                        ).pack()
                    ),
                ]
            ])
        )
    except Exception as ex_:
        logging.critical(ex_)