import asyncio
from datetime import datetime
import logging
import pandas as pd
import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile,\
    InlineKeyboardMarkup, InlineKeyboardButton

from tools.callbacks import StateCallback
from tools.database import Database
from tools.formatter import form_move_btns
from tools.keyboard import actions_with_user_for_own_ikb,\
    actions_with_user_ikb, cancel_btn
from tools.text import STATUSES
from tools.states import ActionWithUsersState


admins_ikbs = {
    "owner": actions_with_user_for_own_ikb, "admin": actions_with_user_ikb
}
admin_router = Router()


@admin_router.message(Command("get_users"))
async def get_users(message: Message, db: Database):
    tg_id = message.from_user.id
    _, count = await db.users.get(
        {"tg_id": tg_id, "status": {"$in": ["owner", "admin"]}}, {"_id": 1})
    
    if count < 1:
        return
    
    user_cur, count = await db.users.get({}, {"_id": 0})
    users = pd.DataFrame(
        columns=["tg_id", "status", "signed", "last_action_time", "reason"])

    async for user in user_cur:
        users.loc[len(users)] = user

    path = f"tempdata/users{message.from_user.id}.csv"
    users.to_csv(path)

    await message.answer_document(FSInputFile(path))

    try:
        os.remove(path)
    except Exception as ex_:
        logging.error(ex_)


@admin_router.message(Command("send_message"))
async def send_message(message: Message, db: Database):
    user_tg_id = message.from_user.id
    _, count = await db.users.get(
        {"tg_id": user_tg_id, "status": {"$in": ["owner", "admin"]}}, {"_id": 1})
    
    if count < 1:
        return
    
    msg = message.reply_to_message

    if not msg:
        await message.answer(
            "Вам необхідно відповісти командую "
            "на повідомлення, яке бажаєте відправити"
        )
        return

    user_cur, count = await db.users.get({})

    async for user in user_cur:
        try:
            await message.bot.copy_message(
                user["tg_id"], user_tg_id, msg.message_id
            )
        except Exception as ex_:
            logging.info(ex_)
        await asyncio.sleep(0.3)


@admin_router.message(Command("get_orders"))
async def get_orders(message: Message, db: Database):
    user_tg_id = message.from_user.id
    _, count = await db.users.get(
        {"tg_id": user_tg_id, "status": {"$in": ["owner", "admin"]}}, {"_id": 1})
    
    if count < 1:
        return
    
    orders_cur, _ = await db.orders.get({}, {"_id": 0})
    orders = pd.DataFrame(
        columns=["customer_tg_id", "ordered_time", "text", "status", "reason"])
    
    async for order in orders_cur:
        orders.loc[len(orders)] = order

    path = f"tempdata/orders{message.from_user.id}.csv"
    orders.to_csv(path)

    await message.answer_document(FSInputFile(path))

    try:
        os.remove(path)
    except Exception as ex_:
        logging.error(ex_)


# @admin_router.message(Command("delete_orders"))
# async def delete_orders(message: Message, db: Database):
#     user_tg_id = message.from_user.id
#     _, count = await db.users.get(
#         {"tg_id": user_tg_id, "status": {"$in": ["owner", "admin"]}}, {"_id": 1})
    
#     if count < 1:
#         return




# select user action


@admin_router.message(Command("select_user"))
async def select_user(message: Message, state: FSMContext, db: Database):
    tg_id = message.from_user.id
    users, count = await db.users.get(
        {"tg_id": tg_id, "status": {"$in": ["admin", "owner"]}})
    
    if count < 1:
        return
    
    user: dict = (await users.to_list(1))[0]
    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", 
            "msg": "cancel_user_selection", 
            "data": "cancel_user_selection"
        },
        next_data_list={
            "action": "next", 
            "msg": "set_action_description",
            "data": "set_action_description"
        }
    )

    await state.set_state(ActionWithUsersState.set_user_id)
    msg = await message.answer(
        text="Внесіть ідентифікатор користувача",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await state.update_data(
        {"msg_id": msg.message_id, "adm_status": user["status"]})
    

@admin_router.message(ActionWithUsersState.set_user_id)
async def set_user_id(message: Message, state: FSMContext, db: Database):
    tg_id = message.text

    try:
        tg_id = int(tg_id)
    except:
        pass

    users, count = await db.users.get(
        {"tg_id": tg_id, "status": {"$ne": "owner"}})

    if count < 1:
        msg = await message.answer("Такого користувача немає в базі даних")
        await asyncio.sleep(5)
        await message.delete()
        await msg.delete()
        return

    user: dict = (await users.to_list(1))[0]
    storage_data = await state.get_data()
    msg_id = storage_data.get("msg_id")
    status = storage_data.get("adm_status")

    if user.get("status") == "admin" and status == "admin":
        msg = await message.answer(
            "Ви не маєте права проводити операції з цим користувачем"
        )
        await asyncio.sleep(5)
        await message.delete()
        await msg.delete()
        return

    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", 
            "msg": "cancel_user_selection", 
            "data": "cancel_user_selection"
        },
        next_data_list={
            "action": "next", 
            "msg": "set_action_description",
            "data": "set_action_description"
        }
    )

    await state.update_data({"user_tg_id": tg_id})
    await message.bot.edit_message_text(
        text=f"Користувач: <a href='tg://user?id={tg_id}'>{tg_id}</a>",
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )
    await message.delete()


@admin_router.callback_query(
    StateCallback.filter((F.msg == "set_user_id") & (F.action == "back")),
    ActionWithUsersState.set_description
)
async def set_user_id_callback(callback: CallbackQuery, state: FSMContext):
    storage_data = await state.get_data()
    tg_id = storage_data.get("user_tg_id")

    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", 
            "msg": "cancel_user_selection", 
            "data": "cancel_user_selection"
        },
        next_data_list={
            "action": "next", 
            "msg": "set_action_description",
            "data": "set_action_description"
        }
    )

    await state.update_data({"user_tg_id": tg_id})
    await callback.message.edit_text(
        text=f"Користувач: <a href='tg://user?id={tg_id}'>{tg_id}</a>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@admin_router.callback_query(
    StateCallback.filter(F.msg == "set_action_description")
)
async def set_description_text(callback: CallbackQuery, state: FSMContext):
    storage_data = await state.get_data()
    tg_id = storage_data.get("user_tg_id")

    if not tg_id:
        await callback.answer(
            text = (
                "Вам необхідно внести ідентифікатор користувача, "
                "щоб продовжити"
            ),
            show_alert=True
        )
        return
    
    reason = storage_data.get("reason") or ""
    status = storage_data.get("adm_status")
    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", 
            "msg": "cancel_user_selection", 
            "data": "cancel_user_selection"
        },
        back_data_list={
            "action": "back", 
            "msg": "set_user_id",
            "data": "set_user_id"
        }
    )

    if not reason:
        reason = f"\n\nПричина дії: {reason}"

    await state.set_state(ActionWithUsersState.set_description)
    await callback.message.edit_text(
        text=f"Користувач: <a href='tg://user?id={tg_id}'>{tg_id}</a>{reason}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=admins_ikbs[status] + btns
        )
    )


@admin_router.message(ActionWithUsersState.set_description)
async def set_description(message: Message, state: FSMContext):
    text = message.text
    storage_data = await state.get_data()
    tg_id = storage_data.get("user_tg_id")
    msg_id = storage_data.get("msg_id")
    status = storage_data.get("adm_status")
    btns = form_move_btns(
        callback_data=StateCallback,
        cancel_data_list={
            "action": "cancel", 
            "msg": "cancel_user_selection", 
            "data": "cancel_user_selection"
        },
        back_data_list={
            "action": "back", 
            "msg": "set_user_id",
            "data": "set_user_id"
        }
    )

    await state.update_data({"reason": text})
    await message.bot.edit_message_text(
        text=(
            f"Користувач: <a href='tg://user?id={tg_id}'>{tg_id}</a>\n"
            f"Причина дії: {text}"
        ),
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=admins_ikbs[status] + btns
        )
    )
    await message.delete()


@admin_router.callback_query(StateCallback.filter(F.msg == "set_action"))
async def set_action(
    callback: CallbackQuery, 
    callback_data: StateCallback, 
    state: FSMContext, 
    db: Database
):
    action = callback_data.data
    storage_data = await state.get_data()
    tg_id = storage_data.get("user_tg_id")
    reason = storage_data.get("reason")
    reason = f"Причина: {reason}" if reason else ""
    status, status_text = STATUSES[action]
    
    await state.clear()
    await db.users.update(
        {"tg_id": tg_id}, {"status": status, "reason": reason}
    )
    await callback.message.edit_text(
        text="Було змінено статус користувача"
    )
    await callback.bot.send_message(
        chat_id=tg_id,
        text=f"{status_text}\n\n{reason}"
    )


@admin_router.callback_query(
    StateCallback.filter(F.msg == "cancel_user_selection")
)
async def cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Дія була відмінена")