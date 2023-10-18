from fastapi import Depends
from typing import List
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from questions.models import Question
from questions.schemas import CreateQuestion, Questions
from db import get_db


class QuestionsRepository:
    """Data Access Layer for operating question info"""

    def __init__(self, db=Depends(get_db)):
        self.db = db

    async def get_all_questions(self) -> List[Questions]:
        query = select(Question)
        questions = self.db.execute(query)
        return [Question.from_orm(question) for question in questions.scalars()]

    async def create_question(self, question: CreateQuestion) -> int:
        new_question = Question(**question.model_dump())
        self.db.add(new_question)
        await self.db.commit()
        return new_question.id

    async def delete_question(self, question_id: int) -> int:
        query = (
            update(Question)
            .where(and_(Question.id == question_id, Question.is_active == True))
            .values(is_active=False)
            .returning(Question.id)
        )

        res = await self.db.execute(query)
        deleted_question_id = res.fetchone()
        if deleted_question_id:
            return deleted_question_id[0]

    async def get_question_by_id(self, question_id: int) -> Questions:
        query = select(Question).where(Question.id == question_id)
        question = await self.db.execute(query)
        return ShowQuestion.from_orm(question.scalar())


