import logging
from typing import List
from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.enums.content_type import ContentType

from service.questions.service import remove_state
from service.auth.service import get_tg_user
from service.admin.service import admin_upload_file, admin_load_clients_from_file, admin_send_mailing
from service.service import create_message_log

from cache.redis import redis_client
from models import UserPermissions

admin_router = Router()
logger = logging.getLogger(__name__)
AccessDeniedMessage = 'Доступ к данному разделу запрещен'


@admin_router.message(Command('admin_upload_file'))
async def admin_upload_file_message(message: types.Message,):
    user = await get_tg_user(message)
    if user.permissions in [UserPermissions.superadmin, UserPermissions.admin]:
        redis_client.set_user_state(message.from_user.id, 'admin_upload_file')
        msg = await message.answer('Привет админ, можешь грузить любой медиа файл')
    else:
        msg = await message.answer(AccessDeniedMessage)
    await create_message_log(msg, user)


@admin_router.message(Command('load_users_from_file_salebot'))
async def admin_load_clients_message(message: types.Message,):
    user = await get_tg_user(message)
    if user.permissions in [UserPermissions.superadmin, UserPermissions.admin]:
        redis_client.set_user_state(message.from_user.id, 'load_users_from_file')
        msg = await message.answer('Привет админ, можешь грузить файл c клиентами')
    else:
        msg = await message.answer(AccessDeniedMessage)
    await create_message_log(msg, user)


@admin_router.message(Command('clean_states'))
async def clean_upload_file_state(message: types.Message):
    redis_client.delete_user_state(message.from_user.id)
    user = await get_tg_user(message)
    await remove_state(user.tg_id)
    msg = await message.answer(text="Убрал все ваши состояния")
    await create_message_log(msg, user)


@admin_router.message(Command('mailing'))
async def mailing_all_users(message: types.Message):
    user = await get_tg_user(message)
    if user.permissions in [UserPermissions.superadmin, UserPermissions.admin]:
        last_draft_key, result = redis_client.get_last_draft(message.from_user.id)
        if last_draft_key:
            msg = await message.answer("У вас уже есть незавершенные рассылки. Хотите завершить их или создать новую ?")
        else:
            redis_client.set_user_state(message.from_user.id, 'mailing_all_users:step_1')
            msg = await message.answer('Привет админ, какое сообщение хочешь отправить ?')
    else:
        msg = await message.answer(AccessDeniedMessage)
    await create_message_log(msg, user)


@admin_router.message(F.video_note | F.video | F.document | F.photo | F.sticker)
async def admin_get_file_id(message: types.Message,):
    user = await get_tg_user(message)
    user_state = redis_client.get_user_state(message.from_user.id)
    if user_state == "admin_upload_file":
        msg = await admin_upload_file(message)
        await create_message_log(msg, user)

    if user_state == "load_users_from_file":
        msg = await admin_load_clients_from_file(message)
        await create_message_log(msg, user)

