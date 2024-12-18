import asyncio
import logging
from collections import deque
from email.message import Message
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
    send = "написал(а)"
    if m.reply_to_message is not None:
        send = f"ответил(а) на сообщение {m.reply_to_message.from_user.full_name}"

    if m.content_type == ContentType.TEXT:
        return f"{m.from_user.full_name} {send}: " + m.text

    if m.caption == "":
        if send == "написал(а)": send = "отправил(а)"
        ans = f"{m.from_user.full_name} {send} {str(m.content_type)[:12]}"
        if m.content_type == ContentType.STICKER:
            ans += f"({m.sticker.emoji})"
        return ans

    ans = f'{m.from_user.full_name} {send}: "{m.caption}"'
    if m.content_type != ContentType.TEXT:
        ans += f" и прикрепил(а) {str(m.content_type)[12:]}"
        if m.content_type == ContentType.STICKER:
            ans += f"({m.sticker.emoji})"
    return str(ans)


@dp.message(Command('start'))
async def start(message: types.Message):
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


@dp.message(F.document)
async def read(message: types.Message):
    file = await bot.get_file(message.document.file_id)  # Получаем информацию о файле
    file_stream = await bot.download_file(file.file_path)  # Загружаем содержимое файла в память

    # file_extension = file_stream.name.split(".")[-1]
    if file_extension != "json": return
    # Читаем содержимое файла
    try:
        data = file_stream.read().decode('utf-8')  # Декодируем файл как текст
        for i in data:
            m = Message(*i)
            print(m)
        # Для проверки выводим содержимое
        await message.answer("Файл успешно обработан!")
    except Exception as e:
        await message.answer(f"Произошла ошибка при чтении файла: {e}")


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
