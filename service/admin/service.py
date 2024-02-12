import logging
import json
from aiogram import types

import config
from cache.redis import redis_client
from models import MailingStatus
from service.admin.load_users import load_users_from_file
from service.service import create_message_log
from utils.markups.static_markup import reply_markup
from repository.admin.repository import create_mailing
from utils.errors.mailing_errors import StepNotFoundError
from service.admin.mailings import get_next_mailing_step, send_mailing_to_users, rollback_mailing, MailingSteps
logger = logging.getLogger(__name__)


async def admin_load_clients_from_file(message: types.Message):
    file = message.document
    msg = 'Неразрешенный формат загрузки пользователей или не предоставлен документ'
    if file and file.mime_type in config.AcceptableFormats:
        msg = 'Возникли проблемы с загрузкой пользователей'
        if await load_users_from_file(message):
            msg = 'Загрузка пользователей успешно завершена'
            logger.info(msg)
            return await message.answer(msg)
        logger.warning(msg)
    return await message.answer(msg)


async def admin_upload_file(message: types.Message, ):
    if message.photo:
        msg = await message.answer(text=f"Вот ваша фотография <code>{message.photo[-1].file_id}</code>",
                              parse_mode="HTML")
        return msg
    if message.document:
        msg = await message.answer(text=f"Вот ваш документ <code>{message.document.file_id}</code>",
                              parse_mode="HTML")
        return msg
    if message.video:
        msg = await message.answer(text=f"Вот ваше видео <code>{message.video.file_id}</code>",
                              parse_mode="HTML")
        return msg
    if message.video_note:
        msg = await message.answer(text=f"Вот ваше видео (кружочек) <code>{message.video_note.file_id}</code>",
                              parse_mode="HTML")
        return msg
    if message.sticker:
        msg = await message.answer(text=f"Вот ваш стикер <code>{message.sticker.file_id}</code>",
                              parse_mode="HTML")
        return msg


async def admin_send_mailing(message: types.Message, user):
    user_state = redis_client.get_user_state(message.from_user.id)
    mailing_step = user_state.split(':')[1].split('_')[1]

    try:
        mailing_step = int(mailing_step)
        step = await get_next_mailing_step(message, mailing_step)
        if not step:
            raise StepNotFoundError
    except (ValueError, StepNotFoundError):
        msg = await message.answer("Произошла ошибка в создании рассылки")
        await create_message_log(msg, user)
        return

    last_draft_key, result = redis_client.get_last_draft(user.id)
    mailing = {}
    draft_key = f"mailing_draft:{user.id}:1"
    if last_draft_key:
        draft_key = f"mailing_draft:{user.id}:{last_draft_key.split(':')[-1]}"
        mailing = json.loads(redis_client.get(draft_key) or "{}")

    if step == MailingSteps.mailing_create.value:
        mailing.update({
            "message": message.text,
            "status": MailingStatus.DRAFT.value
        })
        markup = await reply_markup(["Сохранить рассылку", "Отменить рассылку"])
        msg = await message.answer("Сохранить рассылку?", reply_markup=markup)
        await create_message_log(msg, user)

    elif step == MailingSteps.mailing_save_to_db.value:
        mailing_db = await create_mailing(text=mailing["message"], user=user)
        mailing.update({
            "status": MailingStatus.DRAFT.value,
            "message_id": mailing_db.id
        })
        markup = await reply_markup(["Запустить рассылку", "Протестировать рассылку"])
        msg = await message.answer("Статус рассылки - Черновик. Хотите запустить рассылку ?", reply_markup=markup)
        await create_message_log(msg, user)

    elif step == MailingSteps.mailing_add_new_draft.value:
        draft_number = int(last_draft_key.split(':')[-1]) + 1
        draft_key = f"mailing_draft:{user.id}:{draft_number}"
        mailing = {
            "message": message.text,
            "status": MailingStatus.DRAFT.value
        }

    elif step == MailingSteps.mailing_test_draft.value:
        msg = await message.answer(result["message"])
        await create_message_log(msg, user)
        markup = await reply_markup(["Запустить рассылку", "Протестировать рассылку"])
        msg = await message.answer("Статус рассылки - Черновик. Хотите запустить рассылку ?", reply_markup=markup)
        await create_message_log(msg, user)

    elif step == MailingSteps.mailing_start.value:
        mailing.update({
            "status": MailingStatus.ACTIVE.value
        })
        redis_client.set(draft_key, json.dumps(mailing))

        # Отправка сообщения всем пользователям
        await send_mailing_to_users(message, mailing["message"], mailing)
        mailing.update({
            "status": MailingStatus.CLOSED.value
        })
        # TODO: разбить говнокод количество минут в конфиг вынести
        markup = await reply_markup(["Закрыть рассылку", "Откатить рассылку"])
        msg = await message.answer(
            "Рассылка завершена, хотите зарыть рассылку? Отменить рассылку можно в течение 10 минут",
            reply_markup=markup
        )
        await create_message_log(msg, user)

    elif step == MailingSteps.mailing_end.value:
        redis_client.delete(f"mailing_draft:{user.id}:{last_draft_key.split(':')[-1]}")
        msg = await message.answer("Завершаю рассылку и удаляю ее из кэша(это безопасно)")
        await create_message_log(msg, user)
        redis_client.delete_user_state(message.from_user.id)
        redis_client.set_user_state(message.from_user.id, f"mailing_all_users:step_{step}")
        return

    elif step == MailingSteps.mailing_rollback.value:
        msg = await message.answer("Произвожу откат последней рассылки")
        await create_message_log(msg, user)
        redis_client.set_user_state(message.from_user.id, f"mailing_all_users:step_{MailingSteps.mailing_rollback.value}")

        await rollback_mailing(message, mailing)

        msg = await message.answer("Очищаю данные о рассылке. Ее нужно будет делать по новой")
        await create_message_log(msg, user)
        redis_client.delete(f"mailing_draft:{user.id}:{last_draft_key.split(':')[-1]}")
        redis_client.delete_user_state(message.from_user.id)

    elif step == MailingSteps.mailing_cancel.value:
        redis_client.delete(f"mailing_draft:{user.id}:{last_draft_key.split(':')[-1]}")
        msg = await message.answer("Удалил последнюю добавленную рассылку")
        await create_message_log(msg, user)
        redis_client.delete_user_state(message.from_user.id)
        return

    redis_client.set(draft_key, json.dumps(mailing))
    redis_client.set_user_state(message.from_user.id, f"mailing_all_users:step_{step}")

