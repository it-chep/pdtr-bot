from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, Message
from sqlalchemy import select, and_, update
from datetime import datetime
from db import async_session_maker
from models import TgUser, UserPermissions


async def get_phone_markup():
    markup = ReplyKeyboardBuilder()
    phone_button = KeyboardButton(text="Отправить номер телефона", request_contact=True)
    markup.add(phone_button)
    return markup


async def create_tg_user(message: Message):
    try:
        username = f"@{message.from_user.username}"
    except AttributeError:
        username = None
    async with async_session_maker() as session:
        new_user = TgUser(
            tg_id=message.from_user.id,
            name=message.from_user.first_name,
            username=username,
            surname=message.from_user.last_name,
            registration_date=datetime.now(),
            permissions=UserPermissions.user
        )
        session.add(new_user)
        await session.commit()
        return new_user


async def update_tg_user_phone(message: Message):
    async with async_session_maker() as session:
        user = await session.execute(select(TgUser).filter_by(tg_id=message.from_user.id))
        user = user.scalar()

        if user:
            user.phone = message.contact.phone_number
            user.bot_authorization = True

        await session.commit()


async def get_tg_user(message: Message):
    async with async_session_maker() as session:
        user = await session.execute(select(TgUser).filter_by(tg_id=message.chat.id))
        user = user.scalar()
    if not user:
        user = await create_tg_user(message)
    return user


