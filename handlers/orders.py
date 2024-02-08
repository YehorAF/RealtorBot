import asyncio
import bson

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton,\
    InlineKeyboardMarkup

from tools.callbacks import ReqOrderCallback, StateCallback
from tools.database import Database
from tools.states import RejectJobState, BanUserJobState


orders_router = Router()


@orders_router.callback_query(ReqOrderCallback.filter(F.action == "get_job"))
async def get_job(
    callback: CallbackQuery, callback_data: ReqOrderCallback, db: Database
):
    customer_tg_id = callback_data.user_id
    order_id = callback_data.order_id

    _, count = await db.orders.get(
        {"_id": bson.ObjectId(order_id), "status": "process"})
    
    if count < 1:
        await callback.answer(
            text=(
                "Упс... Щось незрозуміле сталось: "
                "це замовлення вже оброблене"
            ),
            show_alert=True
        )
        return
    
    await db.orders.update(
        {"_id": bson.ObjectId(order_id)}, {"status": "allowed"})
    await callback.message.edit_text(
        text=callback.message.text + "\n\nСтатус: прийнято!"
    )
    await callback.bot.send_message(
        chat_id=customer_tg_id,
        text="Ваш запит було прийнято!"
    )


# reject action


@orders_router.callback_query(
    ReqOrderCallback.filter(F.action == "reject_job")
)
async def reject_job(
    callback: CallbackQuery, 
    callback_data: ReqOrderCallback,
    state: FSMContext,
    db: Database
):
    customer_tg_id = callback_data.user_id
    order_id = callback_data.order_id

    _, count = await db.orders.get(
        {"_id": bson.ObjectId(order_id), "status": "process"})
    
    if count < 1:
        await callback.answer(
            text=(
                "Упс... Щось незрозуміле сталось: "
                "це замовлення вже оброблене"
            ),
            show_alert=True
        )
        return
    
    await state.set_state(RejectJobState.write_msg)
    msg = await callback.message.answer(
        text="Опишіть причину відхилення пропозиції",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Надіслати відповідь",
                callback_data=StateCallback(
                    action="send_reject", msg="send_reject", data=order_id
                ).pack()
            )]
        ])
    )
    await state.update_data({
        "customer_tg_id": customer_tg_id, 
        "order_id": order_id, 
        "msg_id": callback.message.message_id,
        "check_msg_id": msg.message_id
    })
    

@orders_router.message(
    RejectJobState.write_msg
)
async def write_rejection(message: Message, state: FSMContext):
    text = message.text

    await state.update_data({"reason": text})

    storage_data = await state.get_data()
    msg_id = storage_data.get("check_msg_id")
    order_id = storage_data.get("order_id")

    await message.bot.edit_message_text(
        text=f"Опишіть причину відхилення пропозиції\n\nПричина: {text}",
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Надіслати відповідь",
                callback_data=StateCallback(
                    action="send_reject", msg="send_reject", data=order_id
                ).pack()
            )]
        ])
    )
    await message.delete()


@orders_router.callback_query(
    StateCallback.filter(F.action == "send_reject"),
    RejectJobState.write_msg
)
async def send_reject(
    callback: CallbackQuery,
    callback_data: StateCallback,
    state: FSMContext,
    db: Database
):
    storage_data = await state.get_data()
    reason = storage_data.get("reason")

    if not reason:
        await callback.answer(
            text="Вам необхідно написати причину відмови від роботи",
            show_alert=True
        )
        return
    
    await state.clear()

    order_id = callback_data.data
    _, count = await db.orders.get(
        {"_id": bson.ObjectId(order_id), "status": "process"})
    
    if count < 1:
        await callback.answer(
            text=(
                "Упс... Щось незрозуміле сталось: "
                "це замовлення вже оброблене"
            ),
            show_alert=True
        )
        return

    msg_id = storage_data.get("msg_id")
    customer_tg_id = storage_data.get("customer_tg_id")

    await db.orders.update(
        {"_id": bson.ObjectId(order_id)}, 
        {"status": "rejected", "reason": reason}
    )
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id, message_id=msg_id)
    await callback.message.edit_text(
        text=(
            f"Було надіслано відповідь\n\nПричина: {reason}"
        )
    )
    await callback.bot.send_message(
        chat_id=customer_tg_id,
        text=f"Ваш запит було відхилено.\n\nПричина: {reason}"
    )


# ban user action


@orders_router.callback_query(
    ReqOrderCallback.filter(F.action == "ban_user")
)
async def ban_user(
    callback: CallbackQuery, 
    callback_data: ReqOrderCallback,
    state: FSMContext,
    db: Database
):
    customer_tg_id = callback_data.user_id
    order_id = callback_data.order_id

    _, count = await db.orders.get(
        {"_id": bson.ObjectId(order_id), "status": "process"})
    
    if count < 1:
        await callback.answer(
            text=(
                "Упс... Щось незрозуміле сталось: "
                "це замовлення вже оброблене"
            ),
            show_alert=True
        )
        return
    
    await state.set_state(BanUserJobState.write_msg)
    msg = await callback.message.answer(
        text="Опишіть причину блокування користувача",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Надіслати відповідь",
                callback_data=StateCallback(
                    action="ban_user", msg="ban_user", data=order_id
                ).pack()
            )]
        ])
    )
    await state.update_data({
        "customer_tg_id": customer_tg_id, 
        "order_id": order_id, 
        "msg_id": callback.message.message_id,
        "check_msg_id": msg.message_id
    })
    

@orders_router.message(
    BanUserJobState.write_msg
)
async def write_ban_reason(message: Message, state: FSMContext):
    text = message.text

    await state.update_data({"reason": text})

    storage_data = await state.get_data()
    msg_id = storage_data.get("check_msg_id")
    order_id = storage_data.get("order_id")

    await message.bot.edit_message_text(
        text=f"Опишіть причину блокування користувача\n\nПричина: {text}",
        chat_id=message.chat.id,
        message_id=msg_id,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Надіслати відповідь",
                callback_data=StateCallback(
                    action="ban_user", msg="ban_user", data=order_id
                ).pack()
            )]
        ])
    )
    await message.delete()


@orders_router.callback_query(
    StateCallback.filter(F.action == "ban_user"),
    BanUserJobState.write_msg
)
async def send_ban(
    callback: CallbackQuery,
    callback_data: StateCallback,
    state: FSMContext,
    db: Database
):
    storage_data = await state.get_data()
    reason = storage_data.get("reason")

    if not reason:
        await callback.answer(
            text="Вам необхідно написати причину блокування користувача",
            show_alert=True
        )
        return
    
    await state.clear()

    order_id = callback_data.data
    _, count = await db.orders.get(
        {"_id": bson.ObjectId(order_id), "status": "process"})
    
    if count < 1:
        await callback.answer(
            text=(
                "Упс... Щось незрозуміле сталось: "
                "це замовлення вже оброблене"
            ),
            show_alert=True
        )
        return

    msg_id = storage_data.get("msg_id")
    customer_tg_id = storage_data.get("customer_tg_id")

    await db.orders.update(
        {"_id": bson.ObjectId(order_id)}, 
        {"status": "rejected", "reason": reason}
    )
    await db.users.update(
        {"tg_id": customer_tg_id}, {"status": "blocked", "reason": reason})
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.message.chat.id, message_id=msg_id)
    await callback.message.edit_text(
        text=(
            f"Було надіслано відповідь\n\nПричина: {reason}"
        )
    )
    await callback.bot.send_message(
        chat_id=customer_tg_id,
        text=f"Вас було заблоковано.\n\nПричина: {reason}"
    )