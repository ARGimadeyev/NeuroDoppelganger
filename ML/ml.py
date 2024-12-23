from __future__ import annotations

import uuid
import pathlib
import asyncio
import jsonlines

from ML.get_training_dataset import get_dataset, modify_chat, get_case
from yandex_cloud_ml_sdk import YCloudML, AsyncYCloudML
from Backend.config import FOLDER_ID, YAUTH, WINDOW_SIZE
from DB.db import parse_chat, cur, get_model_id
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
async_sdk = AsyncYCloudML(folder_id=FOLDER_ID, auth=YAUTH)
sdk = YCloudML(folder_id=FOLDER_ID, auth=YAUTH)

def get_last(chat_id: str) -> list:
    cur.execute(f"SELECT *FROM all{chat_id} ORDER BY id DESC LIMIT {4 * WINDOW_SIZE}")
    all_mes = cur.fetchall()[::-1]
    return parse_chat(all_mes)

def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path

async def create_dataset(dataset_name: str):
    dataset_draft = async_sdk.datasets.from_path_deferred(
        task_type="TextToTextGeneration",
        path="C:/Users/barso/OneDrive/Desktop/Programming Python/NeuroDoppelganger/ML/data_to_train/train.jsonlines",
        upload_format="jsonlines",
        name=dataset_name,
    )
    print("2")
    await dataset_draft.upload(upload_timeout=60)
    print("2")
    dataset = None
    while dataset is None:
        print("52")
        async for ds in async_sdk.datasets.list(name_pattern=dataset_name, status="READY"):
            dataset = ds
            break
        await asyncio.sleep(60)
    print("2")
    return dataset.id


def tune_model(dataset_id, temperature = None, max_tokens = None) -> str:
    train_dataset = sdk.datasets.get(dataset_id)
    base_model = sdk.models.completions("yandexgpt-lite")

    tuned_model = base_model.tune(train_dataset, name=str(uuid.uuid4()))
    tuned_model = tuned_model.configure(temperature=temperature, max_tokens=max_tokens)

    result_uri = tuned_model.uri
    return result_uri

async def add_model(chat_id: str, temperature=None, max_tokens=None):
    dataset = await get_dataset(chat_id)
    with jsonlines.open("C:/Users/barso/OneDrive/Desktop/Programming Python/NeuroDoppelganger/ML/data_to_train/train.jsonlines", mode="w") as f:
        for row in dataset:
            f.write(row)

    ds_hash = str(uuid.uuid4())
    dataset_id = await create_dataset(dataset_name=f"{chat_id}_{ds_hash}")
    print(f"{dataset_id=}: {datetime.now()}")
    model_uri = tune_model(dataset_id, temperature, max_tokens)
    print(f"{model_uri=}: {datetime.now()}")
    return model_uri


def get_response(chat_id, user):
    chat = get_last(chat_id)
    modified_chat, by_id = modify_chat(chat)

    prompt = get_case(modified_chat, modified_chat, by_id, user)["request"]
    # print(prompt)
    model_uri = get_model_id(chat_id)

    model = sdk.models.completions(model_uri)

    result = model.run(prompt)
    response = result.alternatives[0].text
    return response

