from datetime import datetime
from collections import deque
from DB.db import get_messages
from Backend.config import MIN_MESSAGE_THRESHOLD, WINDOW_SIZE, MAX_MESSAGE_DELAY


def add_case(window: deque, result: list, chat: list, by_id: dict) -> None:
    case = dict()
    task = (f"Ты - {window[WINDOW_SIZE - 1]["full_name"]} и участвуешь в переписке. "
            f"Твоя задача - ответить от лица {window[WINDOW_SIZE - 1]["full_name"]}, полностью копируя его манеру речи")
    case["request"] = [{"role": "system", "text": task}]
    for i in range(0, WINDOW_SIZE - 1):
        case["request"].append({"role": window[i]["full_name"], "text": window[i]["text"]})
        if window[i]["id_reply"]:
            txt = f"[Ответ на сообщение {chat[by_id[window[i]["id_reply"]]]}] {case["request"][-1]["text"]}"
            case["request"][-1]["text"] = txt
    case["response"] = window[-1]["text"]
    result.append(case)


def get_dataset(chat_id: int) -> list:
    chat = get_messages(chat_id)
    modified_chat = list()
    by_id = dict()
    for message in chat:
        if modified_chat and message["user_name"] == modified_chat[-1]["user_name"] and not message["id_reply"]:
            if datetime.timestamp(message["mes_date"]) - datetime.timestamp(
                    modified_chat[-1]["mes_date"]) <= MAX_MESSAGE_DELAY:
                modified_chat[-1]["text"] += f"\n{message["text"]}"
                modified_chat[-1]["mes_date"] = message["mes_date"]
                by_id[message["id"]] = len(modified_chat) - 1
                continue
        modified_chat.append(message)
        by_id[message["id"]] = len(modified_chat) - 1

    if len(modified_chat) < WINDOW_SIZE:
        raise IndexError("Chat is too short")

    user_messages_count = dict()
    for message in modified_chat:
        if user_messages_count.get(message["user_name"]):
            user_messages_count[message["user_name"]] += 1
        else:
            user_messages_count[message["user_name"]] = 1

    result = list()
    window = deque(maxlen=WINDOW_SIZE)

    for i in range(WINDOW_SIZE):
        window.append(modified_chat[i])
    if user_messages_count[window[-1]["user_name"]] >= MIN_MESSAGE_THRESHOLD:
        add_case(window, result, modified_chat, by_id)
    for i in range(WINDOW_SIZE, len(modified_chat)):
        window.popleft()
        window.append(modified_chat[i])
        if user_messages_count[window[-1]["user_name"]] >= MIN_MESSAGE_THRESHOLD:
            add_case(window, result, modified_chat, by_id)

    return result
