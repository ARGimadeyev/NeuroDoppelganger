from datetime import datetime
from collections import deque
from DB.db import get_messages
from Backend.config import MIN_MESSAGE_THRESHOLD, WINDOW_SIZE, MAX_MESSAGE_DELAY
import asyncio

def get_case(window, chat: list, by_id: dict) -> dict:
    case = dict()
    task = "Ты участвуешь в переписке ниже и должен отвечать от имени людей, чтобы это выглядело естественно. Полностью копируй их манеру речи."
    chat_text: str = ""
    for elem in window:
        if elem == window[-1]: break
        chat_text += f"[Сообщение от {elem["full_name"]}"
        if elem["id_reply"] and by_id.get(elem["id_reply"]):
            chat_text += f", ответ на сообщение: {chat[by_id[elem["id_reply"]]]["mes_text"]}"
        chat_text += f"] {elem["mes_text"]}\n"
    case["request"] = [{"role": "system", "text": f"{task}\n\n{chat_text}"}, {"role": "user", "text": f"Ответь от лица {window[-1]["full_name"]}"}]
    case["response"] = window[-1]["mes_text"]
    return case


def modify_chat(chat):
    modified_chat = list()
    by_id = dict()
    for message in chat:
        if modified_chat and message["full_name"] == modified_chat[-1]["full_name"] and not message["id_reply"]:
            if datetime.timestamp(message["mes_date"]) - datetime.timestamp(
                    modified_chat[-1]["mes_date"]) <= MAX_MESSAGE_DELAY:
                modified_chat[-1]["mes_text"] += f"\n{message["mes_text"]}"
                modified_chat[-1]["mes_date"] = message["mes_date"]
                by_id[message["id"]] = len(modified_chat) - 1
                continue
        modified_chat.append(message)
        by_id[message["id"]] = len(modified_chat) - 1

    return modified_chat, by_id

def get_dataset(chat_id: int, only_active_users: bool = True) -> list:
    chat = asyncio.run(get_messages(chat_id))
    modified_chat, by_id = modify_chat(chat)

    user_messages_count = dict()
    for message in modified_chat:
        if user_messages_count.get(message["full_name"]):
            user_messages_count[message["full_name"]] += 1
        else:
            user_messages_count[message["full_name"]] = 1

    result = list()
    window = deque(maxlen=WINDOW_SIZE)

    for message in modified_chat:
        while len(window) > WINDOW_SIZE:
            window.popleft()
        window.append(message)
        if user_messages_count[window[-1]["full_name"]] >= MIN_MESSAGE_THRESHOLD or not only_active_users:
            result.append(get_case(window, modified_chat, by_id))

    return result


