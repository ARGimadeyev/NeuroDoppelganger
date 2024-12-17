from collections import deque

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

context = dict()


def add(id: int, message: types.Message):
    if id not in context:
        context[id] = deque()
    context[id].append(message)
    while len(context[id]) > 100:
        context[id].popleft()


@dp.message(Command('start'))
async def start(message: types.Message):
    await message.reply(f"Привет, {message.from_user.full_name}!")


@dp.message(Command('top'))
async def top100(message: types.Message):
    await message.reply(f"id:{message.chat.id}")
    ans = ""
    for s in context[message.chat.id]:
        ans += f"{s.text}  {s.from_user.username}\n"
    await message.answer(ans)


@dp.message()
async def parse(message: types.Message):
    add(message.chat.id, message)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
