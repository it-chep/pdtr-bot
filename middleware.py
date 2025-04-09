from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from routers.auth.routers import request_phone_number, register_user, unauthorized_user
from repository.auth.repository import get_tg_user, check_user_phone, authorize_user, create_tg_user
from utils.utils import normalize_phone_number


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        if isinstance(event, Message):
            user = await get_tg_user(event)

            if not user:
                await create_tg_user(event)
                return await request_phone_number(event)

            contact = event.text
            if hasattr(event, 'contact') and event.contact:
                contact = event.contact.phone_number

            if user and not user.bot_authorization:
                if not normalize_phone_number(contact):
                    return await request_phone_number(event)
                else:
                    if await check_user_phone(contact):
                        user.bot_authorization = True
                        await authorize_user(user, contact)
                        return await register_user(event)
                    else:
                        return await unauthorized_user(event)

        elif isinstance(event, CallbackQuery):
            user = await get_tg_user(event)

            if not user:
                await create_tg_user(event)
                return await request_phone_number(event.message)

            if user and not user.bot_authorization:
                contact = event.data
                if not normalize_phone_number(contact):
                    return await request_phone_number(event.message)
                else:
                    if await check_user_phone(contact):
                        user.bot_authorization = True
                        await authorize_user(user, contact)
                        return await register_user(event.message)
                    else:
                        return await unauthorized_user(event.message)

        return await handler(event, data)
