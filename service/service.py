from db import get_db

from questions.questions import QuestionsRepository
from fastapi import Depends
from questions.schemas import CreateQuestion


class QuestionService:
    def __init__(self, question_repository=Depends(QuestionsRepository)):
        self.question_repository = question_repository

    def get_all_questions(self):
        questions = self.question_repository.get_all_questions()
        return questions

    def create_question(self, question_data: CreateQuestion):
        id = self.question_repository.create_question(question_data)
        return id

    def delete_question(self, question_id):
        return self.question_repository.delete_question(question_id)
