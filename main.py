import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from starlette.responses import HTMLResponse
from questions.schemas import CreateQuestion

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters.command import Command
from routers.questions.routers import question_router
from routers.auth.routers import auth_router
from routers.admin.routers import admin_router

from config import BOT_TOKEN

dp = Dispatcher()
dp.include_router(admin_router)
dp.include_router(auth_router)
dp.include_router(question_router)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/test", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("login/login.html", {"request": request})


@app.post("/RESTAdapter/send_msg_rx/")
async def get_questions(request: Request):
    print(request)
    return HTMLResponse(status_code=200)


async def main():
    bot = Bot(token=BOT_TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print('start bot')
    asyncio.run(main())
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8001)
