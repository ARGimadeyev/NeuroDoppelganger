from collections import deque
from urllib.parse import ParseResult
from aiogram.enums import ParseMode, ContentType
from config import TOKEN

import logging, asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
# from aiogram.types import InlineKeyboardButton, FSInputFile, \
#     InputMediaPhoto
# from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F

# from typing import Optional

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

context = dict()


async def add(_id_: int, message: types.Message):
    if _id_ not in context:
        context[_id_] = deque()
    context[_id_].append(message)
    while len(context[_id_]) > 100:
        context[_id_].popleft()


async def forGPT(m: types.Message):
    send = "написал(а)"
    if m.reply_to_message != None:
        send = f"ответил(а) {m.reply_to_message.from_user.full_name}"
    if m.content_type == ContentType.TEXT:
        return m.text + f" {send} {m.from_user.full_name}"
    if m.text == None:
        ans = f"{m.from_user.full_name} отправил(а) {m.content_type}"
        if m.content_type == ContentType.STICKER:
            ans += f"({m.sticker.emoji})"
        return ans
    ans = f'"{m.text}", {send} {m.from_user.full_name}'
    if m.content_type != ContentType.TEXT:
        ans += f" и {send} {m.content_type}"
        if m.content_type == ContentType.STICKER:
            ans += f"({m.sticker.emoji})"
    return str(ans)


@dp.message(Command('start'))
async def start(message: types.Message):
    await message.reply(f"Привет, {message.from_user.full_name}!")


@dp.message(Command('top'))
async def top100(message: types.Message):
    await message.reply(f"id:{message.chat.id}")
    ans = ""
    if message.chat.id in context:
        for a in context[message.chat.id]:
            ans += await forGPT(a)
            ans += '\n'
        await message.answer(ans)
    else:
        await message.answer("ПУСТО")


@dp.message()
async def parse(message: types.Message):
    await add(message.chat.id, message)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
