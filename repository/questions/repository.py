import asyncio
from typing import List, Tuple

from sqlalchemy import select, and_, update, or_
from sqlalchemy.orm import joinedload
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from cache.redis import redis_client
from models import Message as MessageModel, MessageCondition, AttachmentType, Question
from db import async_session_maker


async def check_answer(message: types.Message, message_text: str, question_number: int) -> Tuple[bool, str, int]:
    async with async_session_maker() as session:
        is_right_answer = True
        current_question = question_number - 1
        answers = []
        #
        # # Объединенный запрос для получения MessageCondition с связанным Question и AttachmentType
        # query = select(MessageCondition).join(
        #     MessageModel, MessageModel.id == MessageCondition.message_to_id
        # ).outerjoin(
        #     AttachmentType, MessageModel.attachment_type_id == AttachmentType.id
        # ).join(
        #     Question, Question.id == MessageCondition.question_id
        # ).where(
        #     MessageCondition.question_id == question_number
        # ).options(
        #     joinedload(MessageCondition.message_to).joinedload(MessageModel.attachment_type),
        #     joinedload(MessageCondition.question)
        # )
        # Предполагаем, что current_question и question_number уже определены


        # Подготовка основного запроса
        query = select(MessageCondition).join(
            MessageModel, MessageModel.id == MessageCondition.message_to_id
        ).outerjoin(
            AttachmentType, MessageModel.attachment_type_id == AttachmentType.id
        ).join(
            Question, Question.id == MessageCondition.question_id
        ).where(
            or_(
                MessageCondition.question_id == question_number,
                MessageCondition.question_id == current_question,
                MessageCondition.question_id is None
            )
        ).options(
            joinedload(MessageCondition.message_to).joinedload(MessageModel.attachment_type),
            joinedload(MessageCondition.question)
        )
        lessons = []
        results = await session.execute(query)
        message_condition = None
        previous_condition = None
        for row in results:
            condition = row[0]

            if condition.question is None:
                lessons.append(condition)

            #  Если это 5 10 15 и тд тест
            if condition.question.next_question_id is None and condition.question_id == question_number:
                # Если ответ правильный, то нужно взять видос след урока
                if str(message_text) == str(condition.question.right_answer):
                    sub_query = select(MessageCondition).join(
                        MessageModel, MessageModel.id == MessageCondition.message_from_id
                    ).outerjoin(
                        AttachmentType, MessageModel.attachment_type_id == AttachmentType.id
                    ).where(
                        MessageCondition.message_from_id == condition.message_to_id
                    ).options(
                        joinedload(MessageCondition.message_to).joinedload(MessageModel.attachment_type),
                        joinedload(MessageCondition.question)
                    ).limit(1)

                    sub_result = await session.execute(sub_query)
                    message_condition = sub_result.scalars().first()
                    break

                else:
                    query = select(MessageCondition).join(
                        MessageModel, MessageModel.id == MessageCondition.message_to_id
                    ).outerjoin(
                        AttachmentType, MessageModel.attachment_type_id == AttachmentType.id
                    ).join(
                        Question, Question.id == MessageCondition.question_id
                    ).where(
                        MessageCondition.message_to_id == condition.message_from_id
                    ).options(
                        joinedload(MessageCondition.message_to).joinedload(MessageModel.attachment_type),
                        joinedload(MessageCondition.question)
                    )
                    result = await session.execute(query)
                    message_condition = result.scalars().first()
                    return False, [str(answer) for answer in message_condition.question.answers], condition.message_from_id

            elif condition.question.next_question_id is not None:
                if condition.question_id == current_question:
                    previous_condition = condition
                else:
                    message_condition = condition

        # Проверяем, найдено ли условие и есть ли вопрос
        if not message_condition:
            return None, answers, -1

        if message_condition.question:
            question = message_condition.question
            answers = [str(answer) for answer in question.answers]

            # Сравниваем ответ пользователя с правильным ответом
            if str(message_text) == str(previous_condition.question.right_answer):
                # Записываем состояние в redis
                redis_client.set_user_state(message.chat.id, f'question_{question_number + 1}')
                next_message_id = message_condition.message_to_id

            else:
                is_right_answer = False

                # Если ответ неправильный, повторяем вопрос
                redis_client.set_user_state(message.chat.id, f'question_{question_number}')
                next_message_id = message_condition.message_from_id
                message_condition = await session.execute(
                    select(MessageCondition)
                    .options(joinedload(MessageCondition.question))
                    .where(MessageCondition.message_to_id == next_message_id)
                )
                message_condition = message_condition.scalars().first()

                # Проверяем, найдено ли условие и есть ли вопрос
                if not message_condition or not message_condition.question:
                    return None, [], -1

                question = message_condition.question
                answers = [str(answer) for answer in question.answers]
        else:
            next_message_id = message_condition.message_to_id
        # TODO: сделать отправку с задержкой
        if message_condition.delay_before_send:
            await asyncio.sleep(message_condition.delay_before_send)

        return is_right_answer, answers, next_message_id


