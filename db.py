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

conn = psycopg2.connect(
    # здесь нужно указать данные для подключения к бд
)

cur = conn.cursor()

def add_mess(group_id, messages, model_id):
    for mes in messages:
        if mes['type'] == 'service': continue
        is_photo = mes.get("photo", "-")
        if is_photo != '-':
            b = ""
            for s in mes['text_entities']:
                b += s['text']
            b = b.strip()
            if len(b) == 0: continue
            cur.execute(f"INSERT INTO i{group_id} VALUES ('{mes['from_id']}', 'photo', '{b}', '{mes['date']}', '{model_id}')")
            continue
        b = ""
        for s in mes['text_entities']:
            b += s['text']
        b = b.strip()
        if len(b) == 0: continue
        cur.execute(f"INSERT INTO i{group_id} VALUES ('{mes['from_id']}', 'text', '{b}', '{mes['date']}', '{model_id}')")
        if mes['text'] == '' and mes['media_type'] == 'sticker':
            (cur.execute(
                f"INSERT INTO i{group_id} VALUES ('{mes['from_id']}', '{mes['media_type']}', '{mes['sticker_emoji']}', '{mes['date']}', '{model_id}')"))
        elif mes.get("media_type", '-') != '-':
            b = mes['text'].strip()
            if len(b) == 0: continue
            cur.execute(
                f"INSERT INTO i{group_id} VALUES ('{mes['from_id']}', '{mes['media_type']}', '{b}', '{mes['date']}', '{model_id}')")

def add_chat():
    with open('result.json', 'r', encoding='utf-8') as f:
        new_chat = json.load(f)
    model_id = 52 # здесь нужно указать id модели
    cur.execute(
        f"create table i{str(new_chat['id'])} (user_id text, mes_type text, mes_text text, mes_date timestamp without time zone, model_id text);")
    add_mess(str(new_chat['id']), new_chat['messages'], model_id)

add_chat()

conn.commit()

