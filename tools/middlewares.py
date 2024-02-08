from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime
from typing import Union, Callable, Awaitable, Any
import logging

from tools.database import Database


class UserActionsMiddleware(BaseMiddleware):
    def __init__(self, db: Database) -> None:
        self._db: Database = db


    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: dict[str, Any] 
    ):
        dt = datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
        user_tg_id = event.from_user.id
        users, count = await self._db.users.get(
            {"tg_id": user_tg_id}, {"_id": 1, "status": 1})
        
        if count < 1:
            await self._db.users.add_one({
                "tg_id": user_tg_id, 
                "signed": dt,
                "last_action_time": dt,
                "status": "user"
            })
            logging.info(f"add new user {user_tg_id}")
            status = "user"
        else:
            await self._db.users.update(
                {"tg_id": user_tg_id}, {"last_action_time": dt})
            logging.info(f"new user action {user_tg_id}")
            status = (await users.to_list(1))[0]["status"]

        data |= {"db": self._db}

        if status == "blocked":
            return

        try:
            return await handler(event, data)
        except Exception as ex_:
            logging.error(f" error in handler: {ex_}")
    

# class CallbackMiddleware(BaseMiddleware):
#     async def __call__(
#         self,
#         handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
#         event: CallbackQuery,
#         data: dict[str, Any] 
#     ):
#         db: Database = event.bot.db
#         dt = datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
#         user_tg_id = event.from_user.id

#         _, count = await db.users.get({"tg_id": user_tg_id}, {"_id": 1})
        
#         if count < 1:
#             await db.users.add_one({
#                 "tg_id": user_tg_id, 
#                 "signed": dt,
#                 "last_action_time": dt
#             })
#         else:
#             await db.users.update(
#                 {"tg_id": user_tg_id}, {"last_action_time": dt})
            
#         return await handler(event, data)