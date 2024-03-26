import logging

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import Contact
from aiogram.enums.content_type import ContentType
from service.auth.service import get_phone_markup, create_tg_user, update_tg_user_phone, get_tg_user

from cache.redis import redis_client
from service.service import get_built_message, _get_message_by_handler_service
from repository.repository import create_message_log
auth_router = Router()

logger = logging.getLogger(__name__)


# text = ('Приветствую Вас в боте PDTR-специалистов!\n\n'
#         'Прежде чем вы продолжите, Вы можете авторизуйтесь в боте и использовать бота на все 100% '
#         'Нажмите на /registration и следуйте указаниям')
# f"Здравствуйте, {user.name}! Чем планируете заняться ?"
# ext = ('Чтобы авторизоваться в боте,'
#             ' нужно нажать на кнопку "Отправить телефон" внизу на клавиатуре')


# ##############################################
@auth_router.message(Command('start'))
async def start_message(message: types.Message):
    user = await get_tg_user(message)
    await create_message_log(message, user)

    return await get_built_message(
        message=message,
        tg_user_id=message.from_user.id,
        user=user,
        text=message.text
    )


@auth_router.message(Command('registration'))
async def registration_message(message: types.Message):
    user = await get_tg_user(message)

    text = await _get_message_by_handler_service(message.text)
    markup = await get_phone_markup()
    await message.answer(text=text, reply_markup=markup.as_markup())


@auth_router.message(F.contact)
async def save_number(message: types.Message):
    user = await get_tg_user(message)

    await update_tg_user_phone(message=message)
    text = await _get_message_by_handler_service(message.text)
    await message.answer(text=text, reply_markup=start_markup().as_markup())
