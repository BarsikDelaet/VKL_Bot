import asyncio
from aiogram import Bot, Dispatcher
import time

from config import API_TOKEN
from handlers import common, menu  # , what_can_you_do


async def main():
    """ Подключение диспетчера. Включение бота.
    Подключение всего функционала бота. """
    dp = Dispatcher()
    bot = Bot(token=API_TOKEN)  # TODO: делать скрытый токен через secretconfig

    dp.include_router(common.router)  # Обработка команд /start

    dp.include_router(menu.router)  # Обработка кнопок

    #await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    time.sleep(5)
    asyncio.run(main())
