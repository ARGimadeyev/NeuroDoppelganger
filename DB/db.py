import psycopg2
import os
from dotenv import load_dotenv
import sys
sys.path.append("..")
from Backend.main import bot
load_dotenv("../.env")

conn = psycopg2.connect(
    host=os.getenv("HOST"),
    database=os.getenv("DATABASE"),
    user=os.getenv("USER"),
    password=os.getenv("PASSWORD"),
    port=os.getenv("PORT")
)
cur = conn.cursor()

async def get_user_name(user_id):
    try:
        user = await bot.get_chat(user_id)
        return user.username
    except Exception as e:
        print(f"Error: {e}")
        return None

async def get_full_name(user_id):
    try:
        user = await bot.get_chat(user_id)
        return user.full_name
    except Exception as e:
        print(f"Error: {e}")
        return None


async def add_mess(chat_id, messages):
    for u in range(len(messages)):
        mes = messages[u]
        if mes['type'] == 'service': continue
        id_reply = 0  # если это не ответ на сообщение, то 0, иначе id сообщения
        if mes.get("reply_to_message_id", '-') != '-':
            id_reply = mes["reply_to_message_id"]
        user_name = get_user_name(mes['from_id'])
        full_name = get_full_name(mes['from_id'])
        is_photo = mes.get("photo", "-")
        if is_photo != '-':
            b = ""
            for s in mes['text_entities']:
                b += s['text']
            b = b.strip()
            if len(b) == 0: continue
            cur.execute(
                f"INSERT INTO i{chat_id} VALUES ({u + 1}, '{mes['from_id']}', '{user_name}','{full_name}', 'photo', '{b}', {id_reply}, '{mes['date']}')")
            continue
        b = ""
        for s in mes['text_entities']:
            b += s['text']
        b = b.strip()
        if len(b) == 0: continue
        cur.execute(
            f"INSERT INTO i{chat_id} VALUES ({u + 1}, '{mes['from_id']}','{user_name}', '{full_name}','text', '{b}',{id_reply}, '{mes['date']}')")
        if mes['text'] == '' and mes['media_type'] == 'sticker':
            (cur.execute(
                f"INSERT INTO i{chat_id} VALUES ({u + 1}, '{mes['from_id']}', '{user_name}','{full_name}','{mes['media_type']}', '{mes['sticker_emoji']}', {id_reply}, '{mes['date']}'')"))
        elif mes.get("media_type", '-') != '-':
            b = mes['text'].strip()
            if len(b) == 0: continue
            cur.execute(
                f"INSERT INTO i{chat_id} VALUES ({u + 1}, '{mes['from_id']}', '{user_name}','{full_name}','{mes['media_type']}', '{b}', {id_reply}, '{mes['date']}')")


async def add_chat(new_chat, model_id: str):
    # with open('result.json', 'r', encoding='utf-8') as f:
    #     new_chat = json.load(f)
    # здесь нужно указать id модели
    cur.execute(f"insert into get_model_id values ({str(new_chat['id'])}, {model_id})")
    cur.execute(
        f"create table i{str(new_chat['id'])} (id int, user_id text, user_name text, full_name text, mes_type text, mes_text text, id_reply int, mes_date timestamp without time zone);")
    await add_mess(str(new_chat['id']), new_chat['messages'])
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



