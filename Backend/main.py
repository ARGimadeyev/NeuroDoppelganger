import asyncio
import json
import logging, os
from collections import deque
from typing import Optional
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.enums import ContentType
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram.types import FSInputFile, \
    InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import dialogsHistory, LENdialoges, COLchats
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

conn = psycopg2.connect(
    host=os.getenv("HOST"),
    database=os.getenv("DATABASE"),
    user=os.getenv("USER_52"),
    password=os.getenv("PASSWORD"),
    port=os.getenv("PORT"),
    target_session_attrs="read-write"
)
cur = conn.cursor()
context = dict()


async def add(_id_: int, message: types.Message):
    if _id_ not in context:
        context[_id_] = deque()
    context[_id_].append(message)
    while len(context[_id_]) > 100:
        context[_id_].popleft()


async def forGPT(m: types.Message):
    if m.text is not None:
        return f"{m.from_user.username}: {m.text}"
    if m.caption is not None:
        return f"{m.from_user.username}: {m.caption}"
    if m.content_type == ContentType.STICKER:
        return f"{m.from_user.username}: {m.sticker.emoji}"
    return ""


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


def add_mess(chat_id, messages):
    for u in tqdm(range(len(messages))):
        mes = messages[u]
        if mes['type'] == 'service': continue
        id_reply = 0  # если это не ответ на сообщение, то 0, иначе id сообщения
        if mes.get("reply_to_message_id", '-') != '-':
            id_reply = mes["reply_to_message_id"]
        user_name = mes['from_id']
        full_name = mes['from']
        is_photo = mes.get("photo", "-")
        if is_photo != '-':
            b = ""
            for s in mes['text_entities']:
                b += s['text']
            b = b.strip()
            b = b.replace("'", "''")
            if len(b) == 0: continue
            cur.execute(
                f"INSERT INTO i{chat_id} VALUES ('{mes['id']}', '{mes['from_id']}', '{user_name}','{full_name}', 'photo', '{b}', {id_reply}, '{mes['date']}')")
            continue
        b = ""
        for s in mes['text_entities']:
            b += s['text']
        b = b.strip()
        b = b.replace("'", "''")
        if len(b) == 0: continue
        cur.execute(
            f"INSERT INTO i{chat_id} VALUES ('{mes['id']}', '{mes['from_id']}','{user_name}', '{full_name}','text', '{b}',{id_reply}, '{mes['date']}')")
        if mes['text'] == '' and mes['media_type'] == 'sticker':
            (cur.execute(
                f"INSERT INTO i{chat_id} VALUES ('{mes['id']}', '{mes['from_id']}', '{user_name}','{full_name}','{mes['media_type']}', '{mes['sticker_emoji']}', {id_reply}, '{mes['date']}'')"))
        elif mes.get("media_type", '-') != '-' and isinstance(mes['text'], str):
            b = mes['text'].strip()
            b = b.replace("'", "''")
            if len(b) == 0: continue
            cur.execute(
                f"INSERT INTO i{chat_id} VALUES ('{mes['id']}', '{mes['from_id']}', '{user_name}','{full_name}','{mes['media_type']}', '{b}', {id_reply}, '{mes['date']}')")


def in_db(chat_id):
    cur.execute(f"select *from get_model_id where chat_id = '{chat_id}'")
    res = cur.fetchall()
    return len(res)


def count_db(chat_id):
    if in_db(chat_id):
        cur.execute(f"select count(*) from i{chat_id}")
        res = cur.fetchall()
        return res[0][0]
    return 0

def get_model_id(chat_id):
    return 'yandex-gpt'

async def add_chat(new_chat):
    if in_db(str(new_chat['id'])) and len(new_chat['messages']) > COLchats + count_db(new_chat['id']):
        add_mess(str(new_chat['id']), new_chat['messages'])
        cur.execute(f"delete from get_model_id where chat_id = '{str(new_chat['id'])}'")

        model_id = get_model_id(new_chat['id'])  # в этой строке Антон выгружает переписку из БД, затем по ней нужно получить model_id

        cur.execute(f"insert into get_model_id values ({str(new_chat['id'])}, '{model_id}')")
    elif not in_db(str(new_chat['id'])):
        cur.execute(
            f"create table i{str(new_chat['id'])} (id int, user_id text, user_name text, full_name text, mes_type text, mes_text text, id_reply int, mes_date timestamp without time zone);")
        add_mess(str(new_chat['id']), new_chat['messages'])

        model_id = get_model_id(new_chat['id'])  # в этой строке Антон выгружает переписку из БД, затем по ней нужно получить model_id

        cur.execute(f"insert into get_model_id values ({str(new_chat['id'])}, '{model_id}')")
    conn.commit()


async def get_messages(chat_id):
    cur.execute(f"select *from i{chat_id}")
    all_mes = cur.fetchall()
    res = list()
    for row in all_mes:
        b = dict()
        b["id"] = row[0]
        b["user_id"] = row[1]
        b["user_name"] = row[2]
        b["full_name"] = row[3]
        b["mes_type"] = row[4]
        b["mes_text"] = row[5]
        b["id_reply"] = row[6]
        b["mes_date"] = row[7]
        res.append(b)
    return res


@dp.message(F.document)
async def read(message: types.Message):
    file = await bot.get_file(message.document.file_id)  # Получаем информацию о файле
    file_stream = await bot.download_file(file.file_path)  # Загружаем содержимое файла в память

    file_extension = file.file_path.split(".")[-1]
    if file_extension != "json": return
    try:
        data = file_stream.read().decode('utf-8')
        data = json.loads(data)
        await add_chat(data, '1')
        await message.answer("Все ок) Переписка обрабатывается")

    except:
        await message.answer("Произошла ошибка при чтении файла:(")


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
