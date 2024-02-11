import re
import uuid
from typing import Optional, List

from fastapi import HTTPException
from pydantic import BaseModel, constr, validator, EmailStr
from questions.models import Question as QuestionModel

LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")


class TunedModel(BaseModel):
    class Config:
        from_attributes = True


class Questions(TunedModel):
    id: int
    name: str
    body: str
    right_answer: int
    answers: List[int]


class CreateQuestion(TunedModel):
    name: str
    body: str
    right_answer: int
    answers: List[int]

