from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from tools.callbacks import BasicCallback, StateCallback

agent_help_btn = InlineKeyboardButton(
    text="Інше питання⁉️", 
    callback_data=BasicCallback(
        user_action="agent_help", msg="current").pack()
)
dwelling_btn = InlineKeyboardButton(
    text="Купити/Зняти і т.д🏠", 
    callback_data=BasicCallback(
        user_action="dwelling", msg="current").pack()
)

buy_btn = InlineKeyboardButton(
    text="💸Купити", 
    callback_data=BasicCallback(
        user_action="buy", msg="buy_or_rent").pack()
)
rent_btn = InlineKeyboardButton(
    text="🐺Орендувати", 
    callback_data=BasicCallback(user_action="rent", msg="buy_or_rent").pack()
)
sell_btn = InlineKeyboardButton(
    text="🚀Продати", 
    callback_data=BasicCallback(user_action="sell", msg="current").pack()
)
rent_out_btn = InlineKeyboardButton(
    text="🤟Здати в оренду", 
    callback_data=BasicCallback(user_action="rent_out", msg="current").pack()
)

go_to_start_btn = InlineKeyboardButton(
    text="👈Повернутись",
    callback_data=BasicCallback(
        user_action="go_back", msg="start_msg").pack()
)

go_to_actions_btn = InlineKeyboardButton(
    text="👈Повернутись",
    callback_data=BasicCallback(
        user_action="go_back", msg="actions_msg").pack()
)

ban_user_btn = InlineKeyboardButton(
    text="Заблокувати",
    callback_data=StateCallback(
        action="ban_user", msg="set_action", data="ban").pack()
)
unban_user_btn = InlineKeyboardButton(
    text="Розблокувати",
    callback_data=StateCallback(
        action="unban_user", msg="set_action", data="unban").pack()
)
grade_admin_btn = InlineKeyboardButton(
    text="Зробити адміном",
    callback_data=StateCallback(
        action="grade_admin", msg="set_action", data="grade").pack()
)
ungrade_admin_btn = InlineKeyboardButton(
    text="Зняти адмфнку",
    callback_data=StateCallback(
        action="ungrade_admin", msg="set_action", data="ungrade").pack()
)
cancel_btn = InlineKeyboardButton(
    text="Відмінити",
    callback_data=BasicCallback(
        user_action="cancel_action", msg="cancel_action").pack()
)

start_msg_ikb = InlineKeyboardMarkup(
    inline_keyboard=[[dwelling_btn, agent_help_btn]]
)
actions_ikb = InlineKeyboardMarkup(
    inline_keyboard=[
        [buy_btn, sell_btn], 
        [rent_btn, rent_out_btn],
        [go_to_start_btn]
    ]
)
go_to_start_ikb = InlineKeyboardMarkup(inline_keyboard=[[go_to_start_btn]])
towns_buy_list = [
    # InlineKeyboardButton(text="Дніпро", url="https://t.me/perevirenaneruhomistPRODAZHdnipr"),
    InlineKeyboardButton(text="Кам'янське", url="https://t.me/perevirenaneruhomistPRODAZHdndz")
]
towns_rent_list = [
    # InlineKeyboardButton(text="Дніпро", url="https://t.me/perevirenaneruhomistORENDAdnipro"),
    InlineKeyboardButton(text="Кам'янське", url="https://t.me/perevirenaneruhomistORENDAdndz")
]
go_to_actions_ikb = InlineKeyboardMarkup(inline_keyboard=[[go_to_actions_btn]])
actions_with_user_for_own_ikb = [
    [ban_user_btn, unban_user_btn], [grade_admin_btn, ungrade_admin_btn]
]
actions_with_user_ikb = [[ban_user_btn, unban_user_btn]]
cancel_ikb = InlineKeyboardMarkup(inline_keyboard=[[cancel_btn]])