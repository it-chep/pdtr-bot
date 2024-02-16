from datetime import datetime
import logging
from typing import List
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from models import MessageLog, AttachmentType, MessageCondition, MessageButton, Message as MessageModel
from exceptions.data_exceptions import ConditionNotFoundError, MessageNotFoundError
from db import async_session_maker

logger = logging.getLogger(__name__)


# ##########################################################################
async def get_message_by_handler(handler):
    async with async_session_maker() as session:
        # Объединяем запросы для получения сообщения и его типа вложения
        query = select(MessageModel).join(
            MessageCondition, MessageModel.id == MessageCondition.message_to_id
        ).outerjoin(
            AttachmentType, MessageModel.attachment_type_id == AttachmentType.id
        ).filter(
            MessageCondition.condition == handler
        ).options(joinedload(MessageModel.attachment_type))
        message_to_send = await session.execute(query)

        try:
            message_to_send = message_to_send.scalar_one_or_none()
        except Exception:
            raise MessageNotFoundError

        if not message_to_send:
            raise MessageNotFoundError

        return message_to_send


async def get_buttons_by_message_id(message_id: int) -> List[MessageButton]:
    async with async_session_maker() as session:
        result = await session.execute(select(MessageButton).filter_by(message_id=message_id))
        buttons = result.scalars().all()

        for button in buttons:
            ...

        return buttons


async def get_test_inline_buttons(values):
    async with async_session_maker() as session:
        query = select(MessageButton).where(
            MessageButton.action_type_id == 2,
            MessageButton.text.in_(values),
        )
        result = await session.execute(query)
        buttons = result.scalars().all()

        # Обработка кнопок
        inline_buttons = []
        for button in buttons:
            inline_buttons.append(button)

        return inline_buttons


async def create_message_log(sent_message, user, service_message_id=None):
    async with async_session_maker() as session:
        if sent_message is None or not hasattr(sent_message, 'message_id'):
            print("Ошибка: message_id не предоставлен для создания message_log")
            return

        # TODO: добавить тип сообщения
        new_log_entry = MessageLog(
            tg_message_id=sent_message.message_id,
            message_id=service_message_id,
            user_id=user.id,
            timestamp=datetime.now(),
            status='sent'
        )
        session.add(new_log_entry)
        await session.commit()
