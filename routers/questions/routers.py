from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from db import async_session_maker
from sqlalchemy import select, and_, update
from routers.admin.routers import admin_send_mailing, admin_router
from service.questions.service import *
from service.service import *
from models import Message as MessageModel
from models import MessageCondition
from cache.redis import redis_client

question_router = Router()


@question_router.callback_query()
async def any_callback(callback: CallbackQuery):
    user = await get_tg_user(callback.message)
    # TODO: мб в middleware вынести
    await create_message_log(callback.message, user)

    state = redis_client.get_user_state(callback.message.chat.id)
    if state and 'question' in state:
        return await send_next_question(callback.message, callback.data, state, user)
    return await get_built_message(callback.message, user)


@question_router.message(F.text == 'Начать тестирование')
async def question_start(message: types.Message):
    user = await get_tg_user(message)
    await create_message_log(message, user)
    state = redis_client.get_user_state(message.from_user.id)
    if state:
        msg = await message.answer("Тестирование невозможно начать сначала")
        await create_message_log(msg, user)
        return
    return await send_first_question(message, message.text, 'question_1', user)

# TODO: выносим


@question_router.message()
async def message_fork(message: types.Message):
    user = await get_tg_user(message)
    user_state = redis_client.get_user_state(message.from_user.id)

    if user_state and "mailing_all_users" in user_state:
        return await admin_send_mailing(message, user)
    else:
        await any_handler(message)


@question_router.message()
async def any_handler(message: types.Message):
    user = await get_tg_user(message)
    await create_message_log(message, user)

    state = redis_client.get_user_state(message.from_user.id)
    if not state:
        state = await get_last_state(message.chat.id)
    if state and 'question' in state:
        return await send_next_question(message, message.text, state, user)
    return await get_built_message(message, user)

