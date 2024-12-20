from __future__ import annotations
import uuid
import pathlib
import asyncio
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
    dataset = await operation
    return dataset


def tune_model(dataset_id, temperature, max_tokens) -> str:
    train_dataset = sdk.datasets.get(dataset_id)
    base_model = sdk.models.completions("yandexgpt-lite")

    tuned_model = base_model.tune(train_dataset, name=str(uuid.uuid4()))
    tuned_model = tuned_model.configure(temperature=temperature, max_tokens=max_tokens)

    result_uri = tuned_model.uri
    return result_uri


def run_model(model_uri: str, prompt: str):
    model = sdk.models.completions(model_uri)

    result = model.run(prompt)
    return result.alternatives[0].text


def add_model(chat_id: int, temperature=None, max_tokens=None):
    pass
    # dataset = get_dataset(chat_id)
    # print(dataset)
    # with open("data_to_train/train.jsonlines", "w", encoding="utf-8") as f:
    #     for request in dataset:
    #         f.write(f"{request}\n")

    # dataset = asyncio.run(create_dataset(local_path("data_to_train/train.jsonlines")))
    # dataset_id = dataset.id
    # dataset_status = dataset.status
    #
    # print(dataset_status)
    # for dataset in sdk.datasets.list():
    #     print(dataset)
    #
    # print(dataset_id)
    # model_id = tune_model(dataset_id, temperature, max_tokens)

    # return model_id

if __name__ == "__main__":
    pass
    # for dataset in sdk.datasets.list():
    #     dataset.delete()

    # print(add_model(2434120063))