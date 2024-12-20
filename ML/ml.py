from __future__ import annotations
import uuid
from yandex_cloud_ml_sdk import YCloudML, AsyncYCloudML
import asyncio

FOLDER_ID = "b1gkunod3dtj94p8vu0n"
AUTH = "y0_AgAAAABl9s3tAATuwQAAAAEckqnVAAD2ZUFsM4ZABJr-lI1W9ZKbL4Po_w"
async_sdk = AsyncYCloudML(folder_id=FOLDER_ID, auth=AUTH)
sdk = YCloudML(folder_id=FOLDER_ID, auth=AUTH)


async def create_dataset(path_to_requests):
    dataset_draft = async_sdk.datasets.from_path_deferred(
        task_type="RequestsToTuneModel",
        path=path_to_requests,
        upload_format="jsonlines",
        name="sirius",
    )

    operation = await dataset_draft.upload()
    dataset = await operation
    dataset_id = dataset.id
    return dataset_id


def tune_model(dataset_id, temperature, max_tokens):
    train_dataset = sdk.datasets.get(dataset_id)
    base_model = sdk.models.completions("yandexgpt-lite")

    tuned_model = base_model.tune(train_dataset, name=str(uuid.uuid4()))
    tuned_model = tuned_model.configure(temperature=temperature, max_tokens=max_tokens)

    result_uri = tuned_model.uri
    return result_uri


def run_model(model_uri, prompt):
    model = sdk.models.completions(model_uri)

    result = model.run(prompt)
    return result.alternatives[0].text


def add_model(path_to_requests, temperature=None, max_tokens=None):
    dataset_id = create_dataset(path_to_requests)

    model_id = tune_model(dataset_id, temperature, max_tokens)
    return model_id

