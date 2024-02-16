import logging
from repository.questions.repository import *
from service.service import *
from typing import List
from sqlalchemy import select, and_, update
from models import Question, TgUser
from cache.redis import redis_client
from sqlalchemy.orm import joinedload
from db import async_session_maker

logger = logging.getLogger(__name__)


async def send_first_question(message, message_text, state, user):
    question_number = int(state.split('_')[-1])
    # Используем асинхронный контекстный менеджер для работы с сессией
    async with async_session_maker() as session:
        # Запрашиваем условие для текущего вопроса
        result = await session.execute(
            select(MessageCondition)
            .where(MessageCondition.condition == message_text)
            .options(joinedload(MessageCondition.message_to), joinedload(MessageCondition.question))
        )
        message_condition = result.scalars().first()
        # Проверяем, есть ли условие и связанный с ним вопрос
        if not message_condition or not message_condition.question:
            # Обработка ошибки или невозможности найти вопрос
            return await message.answer("Вопрос не найден.")
        logger.info(message_condition, message_condition.question)
        question = message_condition.question
        answers = [str(answer) for answer in question.answers]

        # Обновляем состояние пользователя в Redis
        redis_client.set_user_state(message.chat.id, f'question_{question_number + 1}')

        # Подготовка и отправка сообщения с вопросом и клавиатурой
        next_message_id = message_condition.message_to_id
        msg, markup, parse_mode = await get_message_by_id(next_message_id, values=answers)
        sent_message = await message.answer(msg.text, reply_markup=markup, parse_mode=parse_mode)
        await create_message_log(sent_message, user)
        return


async def send_next_question(message: types.Message, message_text: str, state: str, user: TgUser):
    question_number = state.split('_')[-1]
    try:
        question_number = int(question_number)
    except ValueError:
        # Обработка некорректного номера вопроса
        return
    is_right_answer, answers, next_message_id, lesson = await check_answer(message, message_text, question_number, user)

    if is_right_answer is None:
        return
    elif is_right_answer is False:
        msg = await message.answer('Ответ неверный, попробуйте еще раз')
        await create_message_log(msg, user)

    if not next_message_id:
        return

    # Получение и отправка сообщения
    msg, markup, parse_mode = await get_message_by_id(next_message_id, values=answers)
    await send_message(message, msg, markup, parse_mode, user)

    if lesson:
        answers, next_message_id = await get_question_after_lesson(state)
        msg, markup, parse_mode = await get_message_by_id(next_message_id, values=answers)
        await send_message(message, msg, markup, parse_mode, user)
