from datetime import datetime
from collections import deque
from DB.function import get_chat
from Backend.config import MIN_MESSAGE_THRESHOLD, WINDOW_SIZE, MAX_MESSAGE_DELAY


def add_case(window: deque, result: list) -> None:
    case = dict()
    task = (f"Ты - {window[WINDOW_SIZE - 1]["fullname"]} и участвуешь в переписке. "
            f"Твоя задача - ответить от лица {window[WINDOW_SIZE - 1]["fullname"]}, полностью копируя его манеру речи")
    case["request"] = [{"role": "system", "text": task}]
    for i in range(0, WINDOW_SIZE - 1):
        case["request"].append({"role": window[i]["fullname"], "text": window[i]["text"]})
    case["response"] = window[-1]["text"]
    result.append(case)

def get_dataset(chat_path: str) -> list:
    chat = get_chat(chat_path)
    modified_chat = list()
    index_by_id = dict()
    for message in chat:
        if modified_chat and message["username"] == modified_chat[-1]["username"] and not message.get("id_reply"):
            if datetime.timestamp(message["time"]) - datetime.timestamp(modified_chat[-1]["time"]) <= MAX_MESSAGE_DELAY:
                index_by_id[message["id"]] = modified_chat[-1]["id"]
                modified_chat[-1]["text"] += f"\n{message["text"]}"
                modified_chat[-1]["time"] = message["time"]
                continue
        modified_chat.append(message)

    if len(modified_chat) < WINDOW_SIZE:
        raise IndexError("Chat is too short")

    user_messages_count = dict()
    for message in modified_chat:
        if user_messages_count.get(message["username"]):
            user_messages_count[message["username"]] += 1
        else:
            user_messages_count[message["username"]] = 1


    result = list()
    window = deque(maxlen=WINDOW_SIZE)

    for i in range(WINDOW_SIZE):
        window.append(modified_chat[i])
    if user_messages_count[window[-1]["username"]] >= MIN_MESSAGE_THRESHOLD:
        add_case(window, result)
    for i in range(WINDOW_SIZE, len(modified_chat)):
        window.popleft()
        window.append(modified_chat[i])
        if user_messages_count[window[-1]["username"]] >= MIN_MESSAGE_THRESHOLD:
            add_case(window, result)

    return result
