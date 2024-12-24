import asyncio
import random
import json
import logging, os
from typing import Optional
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.enums import ContentType, ParseMode
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.command import Command
from aiogram.types import FSInputFile, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import dialogsHistory, LENdialoges, COLchats
from DB.db import parse_chat
from ML.ml import get_response
from tqdm import tqdm
from dotenv import load_dotenv
from ML.ml import add_model

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


@dp.message(Command('start'))
async def start(message: types.Message):
    await message.reply(
        f"""Привет, {message.from_user.full_name}!\n Я <b>DoppelBot</b> — ваш нейродвойник!  
Я помогу сделать переписку интереснее и живее. Чтобы всё заработало, сделайте меня администратором группы перед началом!  

<b>Что я умею</b>:  
- /start — запускает бота. Лучше использовать в группе 🤟.  
- /newbot — создаёт нейродвойника для вашей группы 👻.  
- /answer — бот отвечает за указанного участника. Укажите @тег или имя человека, и я всё устрою!  

Добавьте меня в группу и доверьтесь магии общения!""", parse_mode=ParseMode.HTML)


ImportHistory = []
user_data = dict()
st = dict()


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
    await message.edit_media(
        InputMediaPhoto(media=ImportHistory[indx], caption=dialogsHistory[indx], parse_mode=ParseMode.HTML),
        reply_markup=await get_keyboard(indx))


@dp.message(Command('newbot'))
async def newbot(message: types.Message):
    user_data[message.from_user.id] = 0
    await message.answer_photo(photo=ImportHistory[0], caption=dialogsHistory[0], reply_markup=await get_keyboard(0),
                               parse_mode=ParseMode.HTML)


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
        b = ""
        for s in mes['text_entities']:
            b += s['text']
        b = b.strip()
        if b:
            b = b.replace("'", "''")
        if len(b) == 0: continue
        cur.execute(
            f"INSERT INTO i{chat_id} VALUES ('{mes['id']}', '{mes['from_id']}','{user_name}', '{full_name}','text', '{b}',{id_reply}, '{mes['date']}')")
        if is_photo != '-':
            continue
        if mes['text'] == '' and mes['media_type'] == 'sticker':
            (cur.execute(
                f"INSERT INTO i{chat_id} VALUES ('{mes['id']}', '{mes['from_id']}', '{user_name}','{full_name}','{mes['media_type']}', '{mes['sticker_emoji']}', {id_reply}, '{mes['date']}'')"))
        elif mes.get("media_type", '-') != '-' and isinstance(mes['text'], str):
            b = mes['text'].strip()
            if b:
                b = b.replace("'", "''")
            if len(b) == 0: continue
            cur.execute(
                f"INSERT INTO i{chat_id} VALUES ('{mes['id']}', '{mes['from_id']}', '{user_name}','{full_name}','{mes['media_type']}', '{b}', {id_reply}, '{mes['date']}')")


async def in_db(chat_id):
    cur.execute(
        f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'i{chat_id}');")
    res = cur.fetchall()
    return len(res) and len(res[0]) and res[0][0] == True


async def in_all_db(chat_id):
    cur.execute(
        f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'all{chat_id}');")
    res = cur.fetchall()
    return len(res) and len(res[0]) and res[0][0] == True


async def count_db(chat_id):
    if await in_db(chat_id):
        cur.execute(f"select count(*) from i{chat_id}")
        res = cur.fetchall()
        return res[0][0]
    return 0


async def add_chat(new_chat):
    count_new_mes = 0
    for e in new_chat['messages']:
        if e['type'] != 'service':
            count_new_mes += 1
    if await in_db(new_chat['id']) and count_new_mes > COLchats + await count_db(new_chat['id']):
        cur.execute(f"delete from i{str(new_chat['id'])}")
        add_mess(str(new_chat['id']), new_chat['messages'])
        cur.execute(f"delete from get_model_id where chat_id = '{str(new_chat['id'])}'")

        model_id = await add_model(chat_id=new_chat['id'],bot=bot)
        # в этой строке Антон выгружает переписку из БД, затем по ней нужно получить model_id
        print(model_id)
        cur.execute(f"insert into get_model_id values ({str(new_chat['id'])}, '{model_id}')")
    elif not await in_db(new_chat['id']):
        cur.execute(
            f"create table i{str(new_chat['id'])} (id text, user_id text, user_name text, full_name text, mes_type text, mes_text text, id_reply text, mes_date timestamp without time zone);")
        if not await in_all_db(new_chat['id']):
            cur.execute(
                f"create table all{str(new_chat['id'])} (id text, user_id text, user_name text, full_name text, mes_type text, mes_text text, id_reply text, mes_date timestamp without time zone);")
        conn.commit()
        add_mess(str(new_chat['id']), new_chat['messages'])
        conn.commit()
        model_id = await add_model(chat_id=new_chat['id'],bot=bot)

        cur.execute(f"insert into get_model_id values ({str(new_chat['id'])}, '{model_id}')")
    conn.commit()


async def get_messages(chat_id):
    cur.execute(f"select *from i{chat_id}")
    all_mes = cur.fetchall()
    return parse_chat(all_mes)


@dp.message(F.document)
async def read(message: types.Message):
    file = await bot.get_file(message.document.file_id)
    file_stream = await bot.download_file(file.file_path)

    file_extension = file.file_path.split(".")[-1]
    if file_extension != "json": return
    try:
        data = file_stream.read().decode('utf-8')
        data = json.loads(data)
        await add_chat(data)
        await message.answer("Все ок) Переписка обрабатывается")
    except Exception as e:
        await message.answer(f"Произошла ошибка при чтении файла:(\n {e}")


async def get_full_name(chat_id, user_name):
    cur.execute(f"select full_name from all{chat_id} where user_name = '{user_name}'")
    res = cur.fetchall()
    if len(res) and len(res[0]):
        return res[0][0]
    return None


@dp.message(Command('answer'))
async def otvet(message: types.Message):
    conn.commit()
    chat_id = str(message.chat.id)[4:]
    if '@' not in message.text:
        try:
            full_name = message.text.split('"')[1]
        except:
            await message.reply("Напишите правильно")
            return
    else:
        try:
            username = message.text.split()[1][1:]
            full_name = await get_full_name(chat_id, username)
        except:
            await message.reply("Напишите правильно")
            return
    if full_name is None:
        await message.reply("Напишите правильно")
        return

    conn.commit()
    try:
        text = get_response(chat_id, full_name)
    except:
        await message.answer("Вы еще не загружали историю этого чата/группы")
        return
    text = text.replace("@NeuroDoppelgangerBot", "")
    text = text.replace("/start", "")
    text = text.replace("/newbot", "")
    if text:
        await message.reply(text + f'\n<b>{full_name}</b>', parse_mode=ParseMode.HTML)


@dp.message()
async def parse(message: types.Message):
    chat_id = str(message.chat.id)[4:]

    if message.chat.id not in st:
        st[message.chat.id] = {"Нейродвойник😎"}

    k = random.randint(1, 6)

    st[message.chat.id].discard(message.from_user.full_name)
    user = random.sample(list(st[message.chat.id]), 1)[0]
    st[message.chat.id].add(message.from_user.full_name)

    if '@' in message.text:
        usern = message.text.split('@')[1]
        usern = usern.split()[0]
        if usern == 'NeuroDoppelgangerBot':
            k = 3
    elif message.reply_to_message:
        if message.reply_to_message.from_user.id == 7992460868:
            k = 3

    conn.commit()
    mes_id = message.message_id
    user_id = 'user' + str(message.from_user.id)
    user_name = str(message.from_user.username)
    full_name = message.from_user.full_name
    mes_type = message.content_type
    mes_text = message.text
    id_reply = 0
    if message.reply_to_message:
        id_reply = message.reply_to_message.message_id
    mes_date = message.date
    if mes_type == ContentType.STICKER:
        mes_text = str(message.sticker.emoji)
    elif message.content_type == ContentType.TEXT:
        mes_text = message.text
    else:
        mes_text = message.caption
    if mes_text:
        mes_text = mes_text.replace("'", "''")
    mes_type = str(mes_type)[12:].lower()
    if not await in_all_db(chat_id):
        cur.execute(
            f"create table all{chat_id} (id text, user_id text, user_name text, full_name text, mes_type text, mes_text text, id_reply text, mes_date timestamp without time zone);")
    cur.execute(
        f"insert into all{chat_id} values ('{mes_id}', '{user_id}', '{user_name}','{full_name}','{mes_type}', '{mes_text}', {id_reply}, '{mes_date}')")
    conn.commit()
    await asyncio.sleep(2)

    if user is None:
        user = "Нейродвойник😎"

    if user == "Нейродвойник😎":
        text = get_response(chat_id, full_name)
    else:
        text = get_response(chat_id, user)
    text = text.replace("@NeuroDoppelgangerBot", "")
    text = text.replace("/start", "")
    text = text.replace("/newbot", "")
    if k == 3 and text:
        await message.reply(text + f'\n<b>{user}</b>', parse_mode=ParseMode.HTML)


async def main():
    await dp.start_polling(bot)


def load():
    for i in range(LENdialoges):
        ImportHistory.append(FSInputFile(f"Backend/ImportHistory/_{i}.png"))


if __name__ == '__main__':
    load()
    asyncio.run(main())
