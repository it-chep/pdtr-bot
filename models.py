from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ARRAY,
    BigInteger,
    DateTime,
    func,
    Boolean,
    ForeignKey,
    Date,
    Time,
    JSON
)
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum
from sqlalchemy_utils.types.choice import ChoiceType
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserPermissions(Enum):
    superadmin = 1
    admin = 2
    user = 3


class MailingStatus(Enum):
    DRAFT = 1
    ACTIVE = 2
    CLOSED = 3


class TgUser(Base):
    __tablename__ = "tg_users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    name = Column(String(255), nullable=False)
    surname = Column(String(255))
    username = Column(String(255))
    phone = Column(String(20))
    give_money = Column(BigInteger)
    registration_date = Column(DateTime, default=func.now())
    permissions = Column(ChoiceType(UserPermissions, impl=Integer()), default=UserPermissions.user)
    bot_authorization = Column(Boolean, default=False)
    site_authorization = Column(Boolean, default=False)
    last_state = Column(Integer)
    lists = Column(ARRAY(Integer))
    extra_data = Column(JSON, nullable=True)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    right_answer = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    answers = Column(ARRAY(Integer), nullable=False)
    next_question_id = Column(Integer, ForeignKey('questions.id'), nullable=True)  # ID следующего вопроса
    next_question = relationship('Question', remote_side=[id])


class Lessons(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_number = Column(Integer)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    file_path = Column(String(255), nullable=True)
    tg_file_id = Column(String(255), nullable=True)
    next_lesson_duration = Column(Integer, nullable=True)  # seconds
    lesson_step = Column(String(255), nullable=True)
    next_step = Column(String(255), nullable=True)


# ##################################################################################################################
class MessageType(Base):
    __tablename__ = "message_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)


class MessageGroup(Base):
    __tablename__ = "message_group"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)


class ButtonType(Base):
    __tablename__ = "button_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)


class ButtonActionType(Base):
    __tablename__ = "button_action_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)


class AttachmentType(Base):
    __tablename__ = "attachment_type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)


class MessageButton(Base):
    __tablename__ = "message_button"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(255), nullable=False)
    button_type_id = Column(Integer, ForeignKey('button_type.id'))
    # example of action_types: reply, url, callback
    action_type_id = Column(Integer, ForeignKey('button_action_type.id'))
    # example of actions: reply - (/start, Hello world) , url - (https://google.com), callback - (2, hello, success)
    button_action = Column(String(255), nullable=False)
    message_id = Column(Integer, ForeignKey('message.id'))  # Принадлежность к сообщению

    button_type = relationship('ButtonType', foreign_keys=[button_type_id])
    action_type = relationship('ButtonActionType', foreign_keys=[action_type_id])


class MessageCondition(Base):
    __tablename__ = "message_condition"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)

    # modifications start
    date = Column(Date, nullable=True)  # Дата отправки
    time = Column(Time, nullable=True)  # Время отправки
    condition = Column(String(255), nullable=True)  # Условие перехода
    variable_for_comparison = Column(String(255), nullable=True)  # Переменная для сравнения
    delay_before_send = Column(Integer, nullable=True)  # Задержка перед ответом в секундах
    variable_to_save = Column(String(255), nullable=True)  # Запомнить ответ в переменную
    need_auth = Column(Boolean, nullable=True)
    # modifications end

    message_from_id = Column(Integer, ForeignKey('message.id'))
    message_to_id = Column(Integer, ForeignKey('message.id'))

    message_from = relationship('Message', foreign_keys=[message_from_id], )
    message_to = relationship('Message', foreign_keys=[message_to_id], )

    question_id = Column(Integer, ForeignKey('questions.id'), nullable=True)
    question = relationship('Question', foreign_keys=[question_id])


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    attachment_type_id = Column(Integer, ForeignKey('attachment_type.id'))
    attachment_id = Column(String(255), nullable=True)
    message_group_id = Column(Integer, ForeignKey('message_group.id'))
    id_in_group = Column(Integer)
    start_message = Column(Boolean, default=False)
    # handler = ...  # may be list of condition
    message_type_id = Column(Integer, ForeignKey('message_type.id'))
    next_messages = Column(ARRAY(Integer), default=[])  # list of messages [message.id, message.id, message.id]

    attachment_type = relationship('AttachmentType', foreign_keys=[attachment_type_id])
    message_group = relationship('MessageGroup', foreign_keys=[message_group_id])
    message_type = relationship('MessageType', foreign_keys=[message_type_id])

    buttons = relationship('MessageButton', cascade='all, delete-orphan')  # list of buttons
    conditions = relationship(
        'MessageCondition',
        foreign_keys="[MessageCondition.message_from_id]",
        cascade='all, delete-orphan'
    )  # list of conditions


class MessageLog(Base):
    __tablename__ = "message_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_message_id = Column(Integer)
    message_id = Column(Integer, ForeignKey('message.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('tg_users.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.now())
    status = Column(String(255), nullable=False)  # Например, 'delivered', 'seen', 'failed', etc.

    message = relationship('Message', foreign_keys=[message_id])
    user = relationship('TgUser', backref='logs')

    def __repr__(self):
        return f"<MessageLog(id={self.id}, message_id={self.message_id}, user_id={self.user_id}, timestamp={self.timestamp}, status='{self.status}')>"


class Mailing(Base):
    __tablename__ = "mailing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Уникальное имя рассылки. Может использоваться для идентификации рассылки в интерфейсе пользователя или логах.
    name = Column(String(255), info={'verbose_name': 'Имя рассылки'})
    # Описание рассылки. Может содержать информацию о цели рассылки, её содержании или любые другие заметки.
    description = Column(Text, info={'verbose_name': 'Описание'})
    # ID создателя рассылки, ссылается на таблицу пользователей (tg_users). Гарантирует, что каждая рассылка имеет
    # создателя.
    creator = Column(Integer, ForeignKey('tg_users.id'), nullable=False, info={'verbose_name': 'Создатель'})
    # Статус рассылки, использует перечисление MailingStatus. Позволяет отслеживать состояние рассылки (например,
    # черновик, активна, завершена).
    status = Column(ChoiceType(MailingStatus, impl=Integer()), default=MailingStatus.DRAFT,
                    info={'verbose_name': 'Статус'})
    # ID сообщения, связанного с рассылкой, ссылается на таблицу сообщений (message). Необязательное поле,
    # может быть использовано для связи рассылки с конкретным сообщением.
    message_id = Column(Integer, ForeignKey('message.id'), nullable=True, info={'verbose_name': 'ID сообщения'})
    # Дата и время начала рассылки. Если не указано, используется время создания записи.
    begin_date = Column(DateTime, default=datetime.now(), info={'verbose_name': 'Дата начала'})
    # Дата и время окончания рассылки. Необязательное поле, может использоваться для автоматического завершения
    # рассылки.
    end_date = Column(DateTime, nullable=True, info={'verbose_name': 'Дата окончания'})
    # Дополнительные данные, связанные с рассылкой. Может использоваться для хранения специфических настроек или
    # параметров рассылки в формате JSON.
    data = Column(JSON, nullable=True, info={'verbose_name': 'Дополнительные данные'})
    # Отношение к модели Message. Позволяет напрямую обращаться к сообщению, связанному с рассылкой, если таковое есть.
    message = relationship('Message', foreign_keys=[message_id], info={'verbose_name': 'Сообщение'})
    # Отношение к модели TgUser. Устанавливает связь между рассылкой и её создателем, позволяет получить доступ к
    # информации о пользователе, создавшем рассылку.
    user = relationship('TgUser', backref='mailings', info={'verbose_name': 'Пользователь'})

    def __repr__(self):
        return f"<Mailing(name={self.name})>"
