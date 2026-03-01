from fastapi import FastAPI
from aiogram import Bot

from flowers.config import BOT_TOKEN_FL

app = FastAPI()
bot = Bot(BOT_TOKEN_FL)
