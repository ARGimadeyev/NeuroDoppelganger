import json
import psycopg2

conn = psycopg2.connect(
        host=HOST,
        database=DATABASE,
        user=USER,
        password=PASSWORD,
        port=PORT
)

with open('result.json', 'r', encoding='utf-8') as f:
    new_chat = json.load(f)

cur = conn.cursor()

def add_mess(group_id, messages):
    for mes in messages:
        if mes['type'] == 'service': continue
        is_photo = mes.get("photo", "-")
        if is_photo != '-':
            b = ""
            for s in mes['text_entities']:
                b += s['text']
            b = b.strip()
            if len(b) == 0: continue
            cur.execute(f"INSERT INTO i{group_id} VALUES ('{mes['from_id']}', 'photo', '{b}', '{mes['date']}')")
            continue
        b = ""
        for s in mes['text_entities']:
            b += s['text']
        b = b.strip()
        if len(b) == 0: continue
        cur.execute(f"INSERT INTO i{group_id} VALUES ('{mes['from_id']}', 'text', '{b}', '{mes['date']}')")
        if mes['text'] == '' and mes['media_type'] == 'sticker':
            (cur.execute(
                f"INSERT INTO i{group_id} VALUES ('{mes['from_id']}', '{mes['media_type']}', '{mes['sticker_emoji']}', '{mes['date']}')"))
        elif mes.get("media_type", '-') != '-':
            b = mes['text'].strip()
            if len(b) == 0: continue
            cur.execute(
                f"INSERT INTO i{group_id} VALUES ('{mes['from_id']}', '{mes['media_type']}', '{b}', '{mes['date']}')")


add_mess(str(new_chat['id']), new_chat['messages'])
conn.commit()

