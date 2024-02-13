import asyncio
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from aiogram import Bot, Dispatcher, types

from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from routers.questions.routers import question_router
from routers.auth.routers import auth_router
from routers.admin.routers import admin_router

dp = Dispatcher()
dp.include_router(admin_router)
dp.include_router(auth_router)
dp.include_router(question_router)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

bot = Bot(token=BOT_TOKEN)

WEBHOOK_FULL_URL = WEBHOOK_URL + WEBHOOK_PATH


@app.get("/")
async def root():
    return {"message": "Hello World"}


async def on_startup():
    await bot.set_webhook(WEBHOOK_FULL_URL)


@app.post(WEBHOOK_PATH)
async def bot_webhook(request: Request):
    update = types.Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_webhook_update(bot=bot, update=update)


@app.on_event("startup")
async def startup_event():
    await on_startup()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
