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

WEBHOOK_FULL_URL = WEBHOOK_URL + WEBHOOK_PATH


@app.get("/")
async def root():
    return {"message": "Hello World"}


async def on_startup(dp: Dispatcher):
    bot = Bot(token=BOT_TOKEN)
    await bot.set_webhook(WEBHOOK_FULL_URL)

print(WEBHOOK_FULL_URL)


@app.post(WEBHOOK_PATH)
async def bot_webhook(request: Request):
    print(request)
    update = types.Update(**await request.json())
    await dp.process_update(update)


@app.on_event("startup")
async def startup_event():
    await on_startup(dp)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)




# async def main():
#     bot = Bot(token=BOT_TOKEN)
#     await dp.start_polling(bot)


# if __name__ == "__main__":
#     print('start bot')
#     asyncio.run(main())

