from sqlalchemy import Column, Integer, String, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    right_answer = Column(Integer, nullable=False)
    answers = Column(ARRAY(Integer), nullable=False)

    @classmethod
    def from_orm(cls, question):
        return cls(
            id=question.id,
            name=question.name,
            body=question.body,
            right_answer=question.right_answer,
            answers=question.answers
        )