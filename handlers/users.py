from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.filters.command import CommandStart

from tools.callbacks import BasicCallback
from tools.keyboard import start_msg_ikb


users_router = Router(name=__name__)


@users_router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="З якого питання вам потрібна кваліфікована допомога?🧐", 
        reply_markup=start_msg_ikb
    )


@users_router.callback_query(BasicCallback.filter(
    (F.user_action == "go_back") & (F.msg == "start_msg")))
async def start_clbk(callback: CallbackQuery):
    await callback.message.edit_text(
        text="З якого питання вам потрібна кваліфікована допомога?🧐",
        reply_markup=start_msg_ikb
    )