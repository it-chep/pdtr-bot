import asyncio
from typing import List, Tuple
from copy import copy
from sqlalchemy import select, and_, update, or_
from sqlalchemy.orm import joinedload
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from repository.repository import create_message_log
from cache.redis import redis_client
from models import Message as MessageModel, MessageCondition, AttachmentType, Question, TgUser
from db import async_session_maker


async def check_answer(
        message: types.Message, message_text: str, seminar_number: int, state_question_number: int, user: TgUser
) -> Tuple[bool, str, int, MessageCondition]:
    is_right_answer = True
    answers = []
    async with async_session_maker() as session:
        current_question = state_question_number - 1

        # ##############################################
        current_condition_query = select(MessageCondition).join(
            MessageModel, MessageModel.id == MessageCondition.message_to_id
        ).outerjoin(
            AttachmentType, MessageModel.attachment_type_id == AttachmentType.id
        ).join(
            Question, Question.id == MessageCondition.question_id
        ).where((MessageCondition.question_number == current_question) & (Question.seminar == seminar_number)).options(
            joinedload(MessageCondition.message_to).joinedload(MessageModel.attachment_type),
            joinedload(MessageCondition.question)
        )

        # ##############################################
        next_condition_query = select(MessageCondition).join(
            MessageModel, MessageModel.id == MessageCondition.message_to_id
        ).outerjoin(
            AttachmentType, MessageModel.attachment_type_id == AttachmentType.id
        ).join(
            Question, Question.id == MessageCondition.question_id
        ).where((MessageCondition.question_number == state_question_number) & (Question.seminar == seminar_number)).options(
            joinedload(MessageCondition.message_to).joinedload(MessageModel.attachment_type),
            joinedload(MessageCondition.question)
        )
        lessons_query = select(MessageCondition).join(
            MessageModel, MessageModel.id == MessageCondition.message_to_id
        ).outerjoin(
            AttachmentType, MessageModel.attachment_type_id == AttachmentType.id
        ).where(MessageCondition.question_id.is_(None)).options(
            joinedload(MessageCondition.message_to).joinedload(MessageModel.attachment_type),
        )
        lessons_query = lessons_query.order_by(MessageCondition.id.asc())

        current_results = await session.execute(current_condition_query)
        next_results = await session.execute(next_condition_query)
        lessons_result = await session.execute(lessons_query)

        lessons = lessons_result.all()

        current_condition = current_results.fetchone()
        if current_condition:
            current_condition = current_condition[0]

        next_condition = next_results.fetchone()
        if next_condition:
            next_condition = next_condition[0]

        lesson = None
        for lesson in lessons:
            lesson = lesson[0]
            if next_condition and lesson.message_to_id == next_condition.message_from_id:
                break
            else:
                lesson = None

        message_condition = current_condition

        # Проверяем, найдено ли условие и есть ли вопрос
        if not message_condition:
            return None, answers, -1, lesson

        next_message_id = None
        if message_condition.question:

            # Сравниваем ответ пользователя с правильным ответом
            if str(message_text) == str(message_condition.question.right_answer):
                # Записываем состояние в redis
                redis_client.set_user_state(message.chat.id, f'question_{seminar_number}_{state_question_number + 1}')
                await set_last_state(message.chat.id, f'question_{seminar_number}_{state_question_number + 1}')
                msg = await message.answer("Ответ верный, так держать!")
                await create_message_log(msg, user)
                if next_condition:
                    question = next_condition.question
                    answers = [str(answer) for answer in question.answers]
                    next_message_id = next_condition.message_to_id
                else:
                    msg = await message.answer(
                        "На этом семинар заканчивается.\nЖдем вас снова 😌"
                    )
                    await create_message_log(msg, user)
            else:
                is_right_answer = False
                lesson = None
                # Если ответ неправильный, повторяем вопрос
                redis_client.set_user_state(message.chat.id, f'question_{seminar_number}_{state_question_number}')
                await set_last_state(message.chat.id, f'question_{seminar_number}_{state_question_number}')
                next_message_id = message_condition.message_to_id
                message_condition = await session.execute(
                    select(MessageCondition)
                    .options(joinedload(MessageCondition.question))
                    .where(MessageCondition.message_to_id == next_message_id)
                )
                message_condition = message_condition.scalars().first()

                # Проверяем, найдено ли условие и есть ли вопрос
                if not message_condition or not message_condition.question:
                    return None, [], -1, lesson

                question = message_condition.question
                answers = [str(answer) for answer in question.answers]
        else:
            next_message_id = message_condition.message_to_id
        if next_condition and next_message_id == next_condition.message_to_id and lesson:
            # Это значит что ответ верный и следующее сообщение - видос
            message_condition = lesson
            next_message_id = lesson.message_to_id
            answers = []
            msg = await message.answer("Тест завершен, ожидайте новый урок.")
            await create_message_log(msg, user)

            if message_condition.delay_before_send:
                await asyncio.sleep(message_condition.delay_before_send)
        return is_right_answer, answers, next_message_id, lesson


async def get_question_after_lesson(state) -> int:
    state_question_number = state.split('_')[-1]
    try:
        state_question_number = int(state_question_number)
        seminar_number = int(state.split('_')[-2])
    except ValueError:
        # Обработка некорректного номера вопроса
        return

    async with async_session_maker() as session:
        condition_query = select(MessageCondition).join(
            MessageModel, MessageModel.id == MessageCondition.message_to_id
        ).outerjoin(
            AttachmentType, MessageModel.attachment_type_id == AttachmentType.id
        ).join(
            Question, Question.id == MessageCondition.question_id
        ).where((MessageCondition.question_number == state_question_number) & (Question.seminar == seminar_number)).options(
            joinedload(MessageCondition.message_to).joinedload(MessageModel.attachment_type),
            joinedload(MessageCondition.question)
        )
        results = await session.execute(condition_query)

        condition = results.fetchone()[0]
        question = condition.question
        answers = [str(answer) for answer in question.answers]

        if condition.delay_before_send:
            await asyncio.sleep(condition.delay_before_send)

        return answers, condition.message_to_id


async def repo_get_last_state(tg_id: int):
    async with async_session_maker() as session:
        query = select(TgUser.last_state).where(TgUser.tg_id == tg_id)
        result = await session.execute(query)
        state = result.fetchone()[0]
        return state


async def set_last_state(tg_id: int, state: str):
    async with async_session_maker() as session:
        query = update(TgUser).where(TgUser.tg_id == tg_id).values(last_state=state)
        await session.execute(query)
        await session.commit()
        return state


async def repo_remove_state(tg_id: int):
    async with async_session_maker() as session:
        query = update(TgUser).where(TgUser.tg_id == tg_id).values(last_state=None)
        await session.execute(query)
        await session.commit()
        return
