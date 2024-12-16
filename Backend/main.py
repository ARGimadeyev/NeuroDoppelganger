from config import TOKEN

import logging, asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
# from aiogram.enums.parse_mode import ParseMode
# from aiogram.client.default import DefaultBotProperties
# from aiogram.types import InlineKeyboardButton, FSInputFile, \
#     InputMediaPhoto
# from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
# from aiogram import F
# from typing import Optional

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command('start'))
async def start(message: types.Message):
    await message.reply("Привет, ты запустил бота")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
