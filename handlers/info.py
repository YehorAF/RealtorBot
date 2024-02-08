from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton,\
    InlineKeyboardMarkup

from tools.callbacks import BasicCallback, StateCallback
from tools.keyboard import (
    actions_ikb, towns_buy_list, towns_rent_list,  
    go_to_start_ikb, go_to_actions_ikb, go_to_actions_btn
)


info_router = Router(name=__name__)


@info_router.callback_query(
    BasicCallback.filter(F.user_action == "agent_help")
)
async def get_agent_help(callback: CallbackQuery):
    await callback.message.edit_text(
        text=(
            "Якщо вам потрібна допомога з іншого питання, "
            "можете мені написати або зателефонувати😉\n\n"
            "✏️@Yurll_Alexandrovlch\n"
            "📱+380 (63) 4162 777"
        ),
        reply_markup=go_to_start_ikb
    )


@info_router.callback_query(BasicCallback.filter(
    (F.user_action == "dwelling") | 
    (F.user_action == "go_back") & 
    (F.msg == "actions_msg")
))
async def get_dwelling_actions(callback: CallbackQuery):
    await callback.message.edit_text(
        text="Натисніть на те, що саме вас цікавить😌",
        reply_markup=actions_ikb
    )


@info_router.callback_query(BasicCallback.filter(
    (F.user_action == "buy") &
    (F.msg == "buy_or_rent")
))
async def buy_or_rent(callback: CallbackQuery, callback_data: BasicCallback):
    action = callback_data.user_action
    btns = [[
        InlineKeyboardButton(
            text="Дивитись усі варіанти",
            callback_data=BasicCallback(
                user_action=action, msg="show_all").pack()
        ),
        InlineKeyboardButton(
            text="Підібрати ідеальний варіант",
            callback_data=StateCallback(
                action=action, msg="select_town", data="create_ref"
            ).pack()
        )
    ], [go_to_actions_btn]]

    await callback.message.edit_text(
        text=(
            "Тут ви можете натиснути «Подивитись усі варіанти» "
            "та зможете побачити усю актуальну нерухомість в обраному "
            "місті або ж, натиснувши на «Підібрати ідеальний варіант», "
            "зможете заповнити запит і сам агент з нерухомості зв‘яжеться "
            "з Вами та зробить найкращу підбірку!"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@info_router.callback_query(BasicCallback.filter(
        (F.user_action == "rent") &
        (F.msg == "buy_or_rent")
))
async def buy_or_rent(callback: CallbackQuery, callback_data: BasicCallback):
    action = callback_data.user_action
    btns = [[
        InlineKeyboardButton(
            text="Підібрати ідеальний варіант",
            callback_data=StateCallback(
                action=action, msg="select_town", data="create_ref"
            ).pack()
        )
    ], [go_to_actions_btn]]

    await callback.message.edit_text(
        text=(
            "Натиснувши на «Підібрати ідеальний варіант», "
            "зможете заповнити запит і сам агент з нерухомості зв‘яжеться "
            "з Вами та зробить найкращу підбірку!"
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btns)
    )


@info_router.callback_query(
    BasicCallback.filter(F.msg == "show_all")
)
async def show_all(callback: CallbackQuery, callback_data: BasicCallback):
    action = callback_data.user_action
    go_back = InlineKeyboardButton(
        text="👈Повернутись",
        callback_data=BasicCallback(
            user_action=action, msg="buy_or_rent"
        ).pack()
    )

    if action == "buy":
        text = "В якому саме місті ви хочете придбати житло?🚀"
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            towns_buy_list, [go_back]
        ])
    else:
        text = "В якому саме місті ви хочете орендувати житло?🐺"
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            towns_rent_list, [go_back]
        ])

    await callback.message.edit_text(text=text, reply_markup=ikb)


@info_router.callback_query(BasicCallback.filter((F.user_action == "sell")))
async def sell_or_rent_out(callback: CallbackQuery):
    await callback.message.edit_text(
        text=(
            "Якщо вам потрібно продати свою нерухомість, "
            "скоріш пишіть або телефонуйте, "
            "і я дам вам кваліфіковану допомогу🤟\n\n"
            "✏️@Yurll_Alexandrovlch\n"
            "📱+380 (63) 4162 777"
        ),
        reply_markup=go_to_actions_ikb
    )


@info_router.callback_query(BasicCallback.filter((F.user_action == "rent_out")))
async def sell_or_rent_out(callback: CallbackQuery):
    await callback.message.edit_text(
        text=(
            "Якщо вам потрібно здати в оренду свою нерухомість, "
            "скоріш пишіть або телефонуйте, "
            "і я дам вам кваліфіковану допомогу🤟\n\n"
            "✏️@Yurll_Alexandrovlch\n"
            "📱+380 (63) 4162 777"
        ),
        reply_markup=go_to_actions_ikb
    )