import json
import psycopg2
from Backend.config import WINDOW_SIZE
from dotenv import load_dotenv
import sys
import os

sys.path.append("..")

load_dotenv("../.env")

conn = psycopg2.connect(
    host=os.getenv("HOST"),
    database=os.getenv("DATABASE"),
    user=os.getenv("USER_52"),
    password=os.getenv("PASSWORD"),
    port=os.getenv("PORT"),
    target_session_attrs="read-write"
)


cur = conn.cursor()

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
    cur.execute(f"SELECT *"
               f"FROM i{chat_id}"
               f"ORDER BY id DESC"
               f"LIMIT {4 * WINDOW_SIZE}"
               )
    all_mes = cur.fetchall()[::-1]
    return modify_chat(all_mes)

conn.commit()
