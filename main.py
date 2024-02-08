import asyncio
import dotenv
import logging
# import ssl
import sys
import os

# from aiohttp import web

from redis.asyncio import Redis

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
# from aiogram.types import FSInputFile
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.methods import DeleteWebhook
from aiogram.webhook.aiohttp_server import SimpleRequestHandler,\
    setup_application

from handlers.info import info_router
from handlers.users import users_router
from handlers.admins import admin_router
from handlers.estate_transactions import estate_transactions_router
from handlers.orders import orders_router
from tools.database import Database
from tools.middlewares import UserActionsMiddleware


# async def on_startup(bot: Bot):
#     url = os.getenv("WEBHOOK_ORIGIN")
#     path = os.getenv("WEBHOOK_PATH")
#     secret = os.getenv("WEBHOOK_SECRET")
#     cert = os.getenv("CERT")

#     await bot.set_webhook(
#         f"{url}/{path}", certificate=FSInputFile(cert), secret_token=secret
#     )


async def on_shutdown(bot: Bot):
    await bot.session.close()


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        # filename="logs/stat.log",
        format=("%(asctime)s - %(module)s - " 
             "%(levelname)s - %(funcName)s: "
             "%(lineno)d - %(message)s"),
        datefmt="%H:%M:%S",
        stream=sys.stdout
    )
    dotenv.load_dotenv("settings/.env")

    # path = os.getenv("WEBHOOK_PATH")
    # secret = os.getenv("WEBHOOK_SECRET")
    token = os.getenv("TOKEN")
    # host = os.getenv("WEBHOOK_HOST")
    # port = os.getenv("WEBHOOK_PORT")
    dburl = os.getenv("DBURL")
    dbname = os.getenv("DBNAME")

    db = Database(dburl, dbname)

    storage = RedisStorage(Redis())

    dp = Dispatcher(storage=storage)
    dp.message.middleware(UserActionsMiddleware(db))
    dp.callback_query.middleware(UserActionsMiddleware(db))
    dp.include_router(users_router)
    dp.include_router(info_router)
    dp.include_router(admin_router)
    dp.include_router(estate_transactions_router)
    dp.include_router(orders_router)
    dp.shutdown.register(on_shutdown)
    # dp.startup.register(on_startup)

    bot = Bot(token=token, parse_mode=ParseMode.HTML)
    
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)

    # app = web.Application()

    # req_handler = SimpleRequestHandler(
    #     dispatcher=dp, 
    #     bot=bot, 
    #     secret_token=secret
    # )
    # req_handler.register(app, path=path)

    # setup_application(app, dp, bot=bot)

    # cert = os.getenv("CERT")
    # key = os.getenv("KEY")

    # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    # context.load_cert_chain(cert, key)

    # web.run_app(app, host=host, port=int(port), ssl_context=context)


if __name__ == "__main__":
    asyncio.run(main())