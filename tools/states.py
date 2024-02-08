from aiogram.fsm.state import State, StatesGroup


class EstateTransactionStates(StatesGroup):
    town = State()
    street = State()
    rooms_amount = State()
    condition = State()
    price = State()
    deadline = State()
    description = State()
    telephone = State()
    agreement = State()
    payment = State()
    check_reference = State()


class RejectJobState(StatesGroup):
    write_msg = State()


class BanUserJobState(StatesGroup):
    write_msg = State()


class BanUserState(StatesGroup):
    set_user_id = State()
    set_description = State()


class UnbanUserState(StatesGroup):
    set_user_id = State()


class ActionWithUsersState(StatesGroup):
    set_user_id = State()
    set_description = State()