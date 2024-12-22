import psycopg2
import os

from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("HOST"),
    database=os.getenv("DATABASE"),
    user=os.getenv("USER_52"),
    password=os.getenv("PASSWORD"),
    port=os.getenv("PORT"),
    target_session_attrs="read-write"
)
cur = conn.cursor()

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

def parse_chat(all_mes) -> list:
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
    return parse_chat(all_mes)

def get_model_id(chat_id):
    cur.execute(f"select model_id from get_model_id where chat_id = '{chat_id}'")
    res = cur.fetchall()
    return res[0][0]

conn.commit()
