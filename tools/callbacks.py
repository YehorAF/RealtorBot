from aiogram.filters.callback_data import CallbackData


class BasicCallback(CallbackData, prefix="bc"):
    user_action: str
    msg: str


class StateCallback(CallbackData, prefix="sc"):
    action: str
    msg: str
    data: str | int


class ReqOrderCallback(CallbackData, prefix="roc"):
    action: str
    user_id: str | int
    order_id: str