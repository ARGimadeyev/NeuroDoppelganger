import json
import psycopg2
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
from aiogram import Bot
from Backend.config import WINDOW_SIZE
import os

COLchats = 100

conn = psycopg2.connect(
    host="rc1a-f5zl0cindthoycb7.mdb.yandexcloud.net,rc1b-imbuhpyfss3w33fz.mdb.yandexcloud.net,rc1d-k0ktcmy3byzzlkqd.mdb.yandexcloud.net",
    database="db1",
    user="user-sirius",
    password="sirius-2024",
    port="6432"
)

cur = conn.cursor()

# user_name - user_id
# full_name - имя контакта

# cur.execute("create table get_model_id (chat_id text, model_id text);")

def add_mess(chat_id, messages):
    for u in range(len(messages)):
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
            if len(b) == 0: continue
            cur.execute(
                f"INSERT INTO i{chat_id} VALUES ({mes['id']}, '{mes['from_id']}', '{user_name}','{full_name}', 'photo', '{b}', {id_reply}, '{mes['date']}')")
            continue
        b = ""
        for s in mes['text_entities']:
            b += s['text']
        b = b.strip()
        if len(b) == 0: continue
        cur.execute(
            f"INSERT INTO i{chat_id} VALUES ({mes['id']}, '{mes['from_id']}','{user_name}', '{full_name}','text', '{b}',{id_reply}, '{mes['date']}')")
        if mes['text'] == '' and mes['media_type'] == 'sticker':
            (cur.execute(
                f"INSERT INTO i{chat_id} VALUES ({mes['id']}, '{mes['from_id']}', '{user_name}','{full_name}','{mes['media_type']}', '{mes['sticker_emoji']}', {id_reply}, '{mes['date']}'')"))
        elif mes.get("media_type", '-') != '-' and isinstance(mes['text'], str):
            b = mes['text'].strip()
            if len(b) == 0: continue
            cur.execute(
                f"INSERT INTO i{chat_id} VALUES ({mes['id']}, '{mes['from_id']}', '{user_name}','{full_name}','{mes['media_type']}', '{b}', {id_reply}, '{mes['date']}')")


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


async def add_chat(new_chat):
    if in_db(str(new_chat['id'])) and len(new_chat['messages']) > COLchats + count_db(new_chat['id']):
        add_mess(str(new_chat['id']), new_chat['messages'])
        cur.execute(f"delete from get_model_id where chat_id = '{str(new_chat['id'])}'")

        model_id = '52'  # в этой строке Антон выгружает переписку из БД, затем по ней нужно получить model_id

        cur.execute(f"insert into get_model_id values ({str(new_chat['id'])}, '{model_id}')")
    elif not in_db(str(new_chat['id'])):
        cur.execute(
            f"create table i{str(new_chat['id'])} (id int, user_id text, user_name text, full_name text, mes_type text, mes_text text, id_reply int, mes_date timestamp without time zone);")
        add_mess(str(new_chat['id']), new_chat['messages'])

        model_id = '52' # в этой строке Антон выгружает переписку из БД, затем по ней нужно получить model_id

        cur.execute(f"insert into get_model_id values ({str(new_chat['id'])}, '{model_id}')")
    conn.commit()


def modify_chat(all_mes) -> list:
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

async def get_messages(chat_id):
    cur.execute(f"select *from i{chat_id}")
    all_mes = cur.fetchall()
    return modify_chat(all_mes)


async def get_last(chat_id: int) -> list:
    cur.execut(f"SELECT *"
               f"FROM i{chat_id}"
               f"ORDER BY id DESC"
               f"LIMIT {4 * WINDOW_SIZE}"
               )
    all_mes = cur.fetchall()[::-1]
    return modify_chat(all_mes)

conn.commit()
