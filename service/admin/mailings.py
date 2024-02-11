from enum import Enum
import logging
from aiogram import types

from service.service import create_message_log

from repository.admin.repository import (
    get_all_users,
    get_logs_from_mailing_by_message_id,
    get_message_by_mailing_id,
    get_mailing_logs_ids
)
from cache.redis import redis_client

from utils.errors.mailing_errors import StepNotFoundError
logger = logging.getLogger(__name__)


class MailingSteps(Enum):
    mailing_create = 1
    mailing_save_to_db = 2
    mailing_test_draft = 3
    mailing_start = 4
    mailing_add_new_draft = 5
    mailing_end = 6
    mailing_cancel = 7
    mailing_rollback = 8


async def get_next_mailing_step(message: types.Message, mailing_step: int):
    if message.text == "Сохранить рассылку" and mailing_step == MailingSteps.mailing_create.value:
        return MailingSteps.mailing_save_to_db.value
    if message.text == "Отменить рассылку" and mailing_step == MailingSteps.mailing_create.value:
        return MailingSteps.mailing_cancel.value
    if message.text == "Запустить рассылку" and (
            mailing_step == MailingSteps.mailing_save_to_db.value
            or
            mailing_step == MailingSteps.mailing_test_draft.value
    ):
        return MailingSteps.mailing_start.value
    if message.text == "Протестировать рассылку" and (
            mailing_step == MailingSteps.mailing_save_to_db.value
            or
            mailing_step == MailingSteps.mailing_test_draft.value
    ):
        return MailingSteps.mailing_test_draft.value
    if message.text == "Закрыть рассылку" and mailing_step == MailingSteps.mailing_start.value:
        return MailingSteps.mailing_end.value
    if message.text == "Откатить рассылку" and mailing_step == MailingSteps.mailing_start.value:
        return MailingSteps.mailing_rollback.value
    if not mailing_step or mailing_step == MailingSteps.mailing_create.value:
        return MailingSteps.mailing_create.value


async def send_mailing_to_users(message, message_text, mailing):
    users = await get_all_users()
    for user in users:
        msg = await message.bot.send_message(user.tg_id, message_text)
        service_message = await get_message_by_mailing_id(mailing.get("message_id"))
        logger.info(f"Пользователь {user.name} c никнеймом {user.username} получил сообщение c id {service_message.id}")
        await create_message_log(msg, user, service_message.id)


async def rollback_mailing(message, mailing):
    service_message = await get_message_by_mailing_id(mailing.get("message_id"))
    if not service_message:
        logger.warning("Нет информации о последней рассылке для отмены.")
        return

    logs = await get_mailing_logs_ids(service_message.id)

    for log in logs:
        user_id = log.user.tg_id
        tg_message_id = log.tg_message_id
        try:
            await message.bot.delete_message(chat_id=user_id, message_id=tg_message_id)
            logger.info(f"Сообщение {tg_message_id} для пользователя {user_id} удалено.")
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение {tg_message_id} для пользователя {user_id}: {e}")
