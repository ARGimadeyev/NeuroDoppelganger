import asyncio
import json
import logging
from collections import deque
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.enums import ContentType
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram.types import FSInputFile, \
    InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import TOKEN, dialogsHistory, LENdialoges

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
    if m.text != None:
        return f"{m.from_user.username}: {m.text}"
    if m.caption != None:
        return f"{m.from_user.username}: {m.caption}"
    if m.content_type == ContentType.STICKER:
        return f"{m.from_user.username}: {m.sticker.emoji}"
    return ""


@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer(str(message.from_user.id))
    await message.reply(
        f"Привет, {message.from_user.full_name}!\nЧтобы создать своего нейродвойника для чата напишите /newbot")


ImportHistory = []
user_data = dict()


class NumbersCallbackFactory(CallbackData, prefix="history"):
    action: str
    value: Optional[int] = None


async def get_keyboard(indx: int):
    keyboard = InlineKeyboardBuilder()
    col = 1
    keyboard.button(text="Назад", callback_data=NumbersCallbackFactory(action='history_back', value=-1))
    if indx < LENdialoges - 1:
        col += 1
        keyboard.button(text="Дальше", callback_data=NumbersCallbackFactory(action='history_next', value=1))
    keyboard.adjust(col)
    return keyboard.as_markup()


async def UpdateReplic(message: types.Message, indx: int):
    await message.edit_media(InputMediaPhoto(media=ImportHistory[indx], caption=dialogsHistory[indx]),
                             reply_markup=await get_keyboard(indx))


@dp.message(Command('newbot'))
async def newbot(message: types.Message):
    user_data[message.from_user.id] = 0
    await message.answer_photo(photo=ImportHistory[0], caption=dialogsHistory[0], reply_markup=await get_keyboard(0))


@dp.callback_query(NumbersCallbackFactory.filter())
async def history(call: types.CallbackQuery, callback_data: NumbersCallbackFactory):
    if call.from_user.id not in user_data:
        user_data[call.from_user.id] = 0
    user_data[call.from_user.id] += callback_data.value
    if user_data[call.from_user.id] < 0:
        user_data[call.from_user.id] = 0
        await call.message.delete()
        await newbot(call.message)
    else:
        await UpdateReplic(call.message, user_data[call.from_user.id])


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


arr = []


@dp.message(F.document)
async def read(message: types.Message):
    file = await bot.get_file(message.document.file_id)  # Получаем информацию о файле
    file_stream = await bot.download_file(file.file_path)  # Загружаем содержимое файла в память

    file_extension = file.file_path.split(".")[-1]
    if file_extension != "json": return
    try:
        data = file_stream.read().decode('utf-8')
        data = json.loads(data)
        groupName = data.get("name")
        for message in data["messages"]:
            if message['type'] != 'message' or (
                    type(message['text']) != str and 'sticker_emoji' not in message): continue
            if 'sticker_emoji' not in message:
                if message['text'] == "": continue
                print(message['from_id'] + ': ' + message['text'])
            else:
                print(message['from_id'] + ': ' + message['sticker_emoji'])
    except:
        await message.answer(f"Произошла ошибка при чтении файла:(")


@dp.message()
async def parse(message: types.Message):
    await add(message.chat.id, message)


async def main():
    await dp.start_polling(bot)


def load():
    for i in range(LENdialoges):
        ImportHistory.append(FSInputFile(f"ImportHistory/_{i}.png"))


if __name__ == '__main__':
    load()
    asyncio.run(main())
