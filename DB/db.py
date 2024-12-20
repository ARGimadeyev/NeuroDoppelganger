import psycopg2
import os
from dotenv import load_dotenv
import sys
sys.path.append("..")
from Backend.main import bot
load_dotenv("../.env")

conn = psycopg2.connect(
    host=os.getenv("HOST"),
    database=os.getenv("DATABASE"),
    user=os.getenv("USER"),
    password=os.getenv("PASSWORD"),
    port=os.getenv("PORT")
)
cur = conn.cursor()



