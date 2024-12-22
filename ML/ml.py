from __future__ import annotations
import uuid
import pathlib
import asyncio
import jsonlines
from get_training_dataset import get_dataset
from yandex_cloud_ml_sdk import YCloudML, AsyncYCloudML

FOLDER_ID = "b1gkunod3dtj94p8vu0n"
AUTH = "y0_AgAAAABl9s3tAATuwQAAAAEckqnVAAD2ZUFsM4ZABJr-lI1W9ZKbL4Po_w"
async_sdk = AsyncYCloudML(folder_id=FOLDER_ID, auth=AUTH)
sdk = YCloudML(folder_id=FOLDER_ID, auth=AUTH)

def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path

async def create_dataset(path_to_requests):
    dataset_draft = async_sdk.datasets.from_path_deferred(
        task_type="TextToTextGeneration",
        path=path_to_requests,
        upload_format="jsonlines",
        name="sirius",
    )

    operation = await dataset_draft.upload()
    dataset = operation
    return dataset.id


def tune_model(dataset_id, temperature, max_tokens) -> str:
    train_dataset = sdk.datasets.get(dataset_id)
    base_model = sdk.models.completions("yandexgpt-lite")

    tuned_model = base_model.tune(train_dataset, name=str(uuid.uuid4()))
    tuned_model = tuned_model.configure(temperature=temperature, max_tokens=max_tokens)

    result_uri = tuned_model.uri
    return result_uri


def run_model(chat_id: int):
    dataset = get_dataset(chat_id, False)[-1]
    prompt = f"{dataset["request"][0]["text"]}\n{dataset["response"]}"
    model = sdk.models.completions(model_uri)

    result = model.run(prompt)
    return result.alternatives[0].text


def add_model(chat_id: int, temperature=None, max_tokens=None):
    dataset = get_dataset(chat_id)

    with jsonlines.open("data_to_train/train.jsonlines", mode="w") as f:
        for row in dataset:
            f.write(row)

    dataset_id = asyncio.run(create_dataset(local_path("data_to_train/train.jsonlines")))
    model_id = tune_model(dataset_id, temperature, max_tokens)

    return model_id