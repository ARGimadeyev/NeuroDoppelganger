import os
from dotenv import load_dotenv


load_dotenv()

FOLDER_ID = os.getenv("FOLDER_ID")
YAUTH = os.getenv("YAUTH")

dialogsHistory = [
    '''Экспорт чатов доступен только через Telegram Desktop на компьютере. Скачать Telegram Desktop можно с официального сайта.''',
    '''Выберите группу, историю которой хотите экспортировать.\nНажмите на значок трех точек (⋮) в правом верхнем углу окна (или на иконку в виде стрелки вниз в зависимости от интерфейса).Выберите опцию "Экспорт истории чата".''',
    '''Уберите галочки со всех позиций и нажмите на формат (HTML)''',
    '''Для правильной обработки ваших сообщений, формат файла должен быть JSON. После сохранения файла, оправьте его в этот чат'''
]

LENdialoges = 4
COLchats = 100
# ML parameters
MIN_MESSAGE_THRESHOLD = 10
MAX_MESSAGE_DELAY = 120
WINDOW_SIZE = 50
