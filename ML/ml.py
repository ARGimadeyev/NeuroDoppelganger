from __future__ import annotations
import uuid
import pathlib
import asyncio
from idlelib.rpc import request_queue
import re

from get_training_dataset import get_dataset
from yandex_cloud_ml_sdk import YCloudML, AsyncYCloudML

FOLDER_ID = "b1gkunod3dtj94p8vu0n"
AUTH = "y0_AgAAAABl9s3tAATuwQAAAAEckqnVAAD2ZUFsM4ZABJr-lI1W9ZKbL4Po_w"
async_sdk = AsyncYCloudML(folder_id=FOLDER_ID, auth=AUTH)
sdk = YCloudML(folder_id=FOLDER_ID, auth=AUTH)

def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path

async def create_dataset(path_to_requests, name="sirius_project"):
    dataset_draft = async_sdk.datasets.from_path_deferred(
        task_type="TextToTextGeneration",
        path=path_to_requests,
        upload_format="jsonlines",
        name=name,
    )

    operation = await dataset_draft.upload()
    dataset = await operation
    return dataset.id


def tune_model(dataset_id, temperature=None, max_tokens=None) -> str:
    train_dataset = sdk.datasets.get(dataset_id)
    base_model = sdk.models.completions("yandexgpt-lite")

    tuned_model = base_model.tune(train_dataset, name=str(uuid.uuid4()))
    tuned_model = tuned_model.configure(temperature=temperature, max_tokens=max_tokens)

    result_uri = tuned_model
    return result_uri


def run_model(model_uri: str, prompt):
    model = sdk.models.completions(model_uri)

    result = model.run(prompt)
    return result.alternatives[0].text


async def add_model(chat_id: int, temperature=None, max_tokens=None):
    dataset = get_dataset(chat_id)
    with open("data_to_train/train.jsonlines", "w", encoding="utf-8") as f:
        for request in dataset:
            f.write(f"{request}\n")

    dataset_id = asyncio.run(create_dataset(local_path("data_to_train/train.jsonlines")))
    print(dataset_id)

    for ds in sdk.datasets.list():
        print(ds)
    # model_id = tune_model(dataset_id, temperature, max_tokens)
    #
    # return model_id

if __name__ == "__main__":
    # chat_id = 1592127213
    # dataset = get_dataset(chat_id)
    # with open("data_to_train/train.jsonlines", "w", encoding="utf-8") as f:
    #     for request in dataset:
    #         result = dict()
    #         result["request"] = list()
    #         result["request"].append(request["request"][0])
    #         result["request"].append(dict())
    #         result["request"][1]["role"] = "chat"
    #         for i in range(1, len(request["request"])):
    #             if i == 1:
    #                 result["request"][1]["text"] = f"{request["request"][i]["role"]}: {request["request"][i]["text"]}".replace('"', "").replace("\n", "")
    #             else:
    #                 result["request"][1]["text"] += f"{request["request"][i]["role"]}: {request["request"][i]["text"]}".replace('"', "").replace("\n", "")
    #         result["response"] = request["response"]
    #         result["response"] = result["response"].replace('"', '').replace("\n", "")
    #         f.write(re.sub(r"\\\\", "", f"{result}\n".replace("'", '"').replace("xa0", "")))
    # model_id = "gpt://b1gkunod3dtj94p8vu0n/yandexgpt-lite/latest@tamrbia1ueelig81q7fut"
    # for ds in sdk.datasets.list():
    #     ds.delete()
    dataset_id = "fds430d4ls9u4fuscmne"
    print(tune_model(dataset_id))
