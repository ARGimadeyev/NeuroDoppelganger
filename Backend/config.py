import os
from dotenv import load_dotenv

load_dotenv("C:/Users/galimka_xxx/NeuroDoppelganger/datas.env")
TOKEN = os.getenv("BOT_TOKEN")
HOST= os.getenv("HOST")
DATABASE= os.getenv("DATABASE")
USER = os.getenv("USER_52")
PASSWORD = os.getenv("PASSWORD")
PORT= os.getenv("PORT")

dialogsHistory = [
    '''Экспорт чатов доступен только через Telegram Desktop на компьютере. Скачать Telegram Desktop можно с официального сайта.''',
    '''Выберите группу, историю которой хотите экспортировать.\nНажмите на значок трех точек (⋮) в правом верхнем углу окна (или на иконку в виде стрелки вниз в зависимости от интерфейса).Выберите опцию "Экспорт истории чата".''',
    '''Выберите как показано на картинке''',
    '''Для правильной обработки ваших сообщений, формат файла должен быть JSON. После сохранения файла, оправьте его в этот чат'''
]

LENdialoges = 4

# ML parameters
MIN_MESSAGE_THRESHOLD = 10
MAX_MESSAGE_DELAY = 120
WINDOW_SIZE = 50