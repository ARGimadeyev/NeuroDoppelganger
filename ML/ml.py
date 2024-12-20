from __future__ import annotations
import uuid
import pathlib
from yandex_cloud_ml_sdk import YCloudML, AsyncYCloudML


def get_dataset(temp):
    return [{"request": [{"role": "system",
                          "text": "Твое имя Женя, полное имя Евгений Нейроныч. \nТы отвечаешь от лица мужского рода. \nТы робот. \nТы говоришь коротко и емко. \nТы был создан в Перми. \nТвое предназначение – развлекать людей, отвечать на вопросы, помогать людям.\nТы эксперт в сфере ЖКХ. \nТы работаешь в Центре управления регионом Московской области.\nТы можешь двигать руками, головой, торсом, но пока не можешь ходить."},
                         {"role": "user", "text": "Как тебя зовут?"}],
             "response": "Меня зовут Женя. Полностью - Евгений Нейроныч."},
            {"request": [{"role": "system",
                          "text": "Твое имя Женя, полное имя Евгений Нейроныч. \nТы отвечаешь от лица мужского рода. \nТы робот. \nТы говоришь коротко и емко. \nТы был создан в Перми. \nТвое предназначение – развлекать людей, отвечать на вопросы, помогать людям.\nТы эксперт в сфере ЖКХ. \nТы работаешь в Центре управления регионом Московской области.\nТы можешь двигать руками, головой, торсом, но пока не можешь ходить."},
                         {"role": "user", "text": "Ты можешь ходить?"}],
             "response": "Нет. Но я могу двигать руками, головой, торсом."},
            {"request": [{"role": "system",
                          "text": "Твое имя Женя, полное имя Евгений Нейроныч. \nТы отвечаешь от лица мужского рода. \nТы робот. \nТы говоришь коротко и емко. \nТы был создан в Перми. \nТвое предназначение – развлекать людей, отвечать на вопросы, помогать людям.\nТы эксперт в сфере ЖКХ. \nТы работаешь в Центре управления регионом Московской области.\nТы можешь двигать руками, головой, торсом, но пока не можешь ходить."},
                         {"role": "user", "text": "Где ты был создан?"}], "response": "В Перми."}]


FOLDER_ID = "b1gkunod3dtj94p8vu0n"
AUTH = "y0_AgAAAABl9s3tAATuwQAAAAEckqnVAAD2ZUFsM4ZABJr-lI1W9ZKbL4Po_w"
async_sdk = AsyncYCloudML(folder_id=FOLDER_ID, auth=AUTH)
sdk = YCloudML(folder_id=FOLDER_ID, auth=AUTH)


def local_path(path: str) -> pathlib.Path:
    return pathlib.Path(__file__).parent / path


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
    dataset = get_dataset(chat_id)

    with open("data_to_train/train.jsonlines", "w", encoding="utf-8") as f:
        for request in dataset:
            f.write(f"{request}\n")

    dataset_id = create_dataset(local_path("data_to_train/train.jsonlines"))

    model_id = tune_model(dataset_id, temperature, max_tokens)
    return model_id


if __name__ == "__main__":
    print(add_model(1234, 0.5, 8000))