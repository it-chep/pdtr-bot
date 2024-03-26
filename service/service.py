from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.types import Contact
from aiogram.enums.content_type import ContentType
from sqlalchemy import select, and_, update, or_
from models import MessageLog, MessageCondition, MessageButton, Message as MessageModel
from exceptions.data_exceptions import ConditionNotFoundError, MessageNotFoundError
from service.auth.service import get_phone_markup, create_tg_user, update_tg_user_phone, get_tg_user
from utils.markups.inline_markup import *
from repository.repository import *
from cache.redis import redis_client
from models import Message
import config


# TODO: рефач

async def get_built_message(message: types.Message, tg_user_id: int, user: models.TgUser, text: str):
    msg, markup, parse_mode = await _build_message(tg_user_id, text)
    return await send_message(message, msg, markup, parse_mode, user)


async def send_message(message: types.Message, msg: MessageModel, markup, parse_mode, user):
    if isinstance(msg, str):
        username = message.from_user.username if hasattr(message.from_user, 'username') else ""
        msg = await message.bot.send_message(
            config.TECH_SUPPORT_CHAT,
            text=f"Неопознанное сообщение от {message.chat.first_name} \n@{username} \nUSER-INFO{str(user)}"
        )
        await message.send_copy(config.TECH_SUPPORT_CHAT)
        await create_message_log(msg, user)
        return

    if hasattr(msg, 'attachment_type_id') and msg.attachment_type_id:
        if msg.attachment_type.code == 'photo':
            sent_message = await message.answer_photo(
                photo=msg.attachment_id, caption=msg.text, parse_mode=parse_mode, reply_markup=markup
            )
            await create_message_log(sent_message, user)
            return
        elif msg.attachment_type.code == 'video':
            sent_message = await message.answer_video(
                video=msg.attachment_id, caption=msg.text, parse_mode=parse_mode, reply_markup=markup
            )
            await create_message_log(sent_message, user)
            return
        elif msg.attachment_type.code == 'video-note':
            sent_message = await message.answer_animation(
                animation=msg.attachment_id, parse_mode=parse_mode, reply_markup=markup
            )
            await create_message_log(sent_message, user)
            return
        elif msg.attachment_type.code == 'voice':
            sent_message = await message.answer_audio(
                audio=msg.attachment_id, parse_mode=parse_mode, reply_markup=markup
            )
            await create_message_log(sent_message, user)
            return
        elif msg.attachment_type.code == 'sticker':
            sent_message = await message.answer_sticker(
                sticker=msg.attachment_id
            )
            await create_message_log(sent_message, user)
            return
        elif msg.attachment_type.code == 'document':
            sent_message = await message.answer_document(
                document=msg.attachment_id, caption=msg.text, parse_mode=parse_mode, reply_markup=markup,
            )
            await create_message_log(sent_message, user)
            return
        elif msg.attachment_type.code == 'document':
            sent_message = await message.answer_document(
                document=msg.attachment_id, caption=msg.text, parse_mode=parse_mode, reply_markup=markup,
            )
            await create_message_log(sent_message, user)
            return
        elif msg.attachment_type.code == 'phone':
            sent_message = await message.answer_contact(
                phone_number=msg.attachment_id, first_name=msg.text
            )
            await create_message_log(sent_message, user)
            return
    if hasattr(msg, 'text'):
        msg = msg.text
    sent_message = await message.answer(text=msg, parse_mode=parse_mode, reply_markup=markup)
    await create_message_log(sent_message, user)
    return


# async def get_message_by_condition_id(condition_id: MessageCondition.id):
#     if condition:
#         query = select(MessageCondition.message_to).where(MessageCondition.id == condition_id)


async def get_message_by_id(message_id: Message.id, values=None):
    if not values:
        values = []

    if message_id:
        query = select(Message).where(Message.id == message_id).options(joinedload(Message.attachment_type))
        result = await async_session_maker().execute(query)
        row = result.fetchone()

        buttons = await get_test_inline_buttons(values)
        if row:
            message = row[0]
            # TODO: исправить хардкод
            try:
                markup = await build_markup(buttons, 2)
            except Exception as e:
                logger.error(e)
                return str(e), None, None

            if not markup:
                markup = await clean_markup()
            parse_mode = "HTML"
            return message, markup, parse_mode

        else:
            return str('message id empty_in'), None, None
    else:
        return str('message id empty_out'), None, None


async def _build_message(user_id, handler) -> (str, List[str], str):
    try:
        msg = await _get_message_by_handler_service(handler)
    except (ConditionNotFoundError, MessageNotFoundError) as e:
        logger.error(e)
        return str(e), None, None

    try:
        markup = await _get_markup_by_message_id(msg.id)
    except Exception as e:
        logger.error(e)
        return str(e), None, None
    if not markup:
        markup = await clean_markup()
    parse_mode = "HTML"
    return msg, markup, parse_mode


async def _get_markup_by_message_id(message_id) -> list:
    markup = None

    buttons = await get_buttons_by_message_id(message_id)
    if buttons:
        # Берем первый элемент, потому что кнопки могут быть только 1 типа
        button_type = buttons[0].button_type_id
        markup = await build_markup(buttons, button_type)
    if not markup:
        markup = await clean_markup()
    return markup


async def _get_message_by_handler_service(handler):
    return await get_message_by_handler(handler)
