import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select, and_, update, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import joinedload

from db import async_session_maker
from models import TgUser, UserPermissions, Mailing, MailingStatus, MessageLog, Message


async def save_user_to_db(user_data: dict) -> bool:
    async with async_session_maker() as session:
        async with session.begin():
            # Проверяем, существует ли уже пользователь с таким tg_id
            query = select(TgUser).filter(TgUser.tg_id == user_data["tg_id"])
            try:
                existing_user = await session.execute(query)
                existing_user = existing_user.scalar_one()
            except NoResultFound:
                existing_user = None

            if existing_user:
                existing_user.name = user_data.get("name", existing_user.name)
            else:
                # Создаем нового пользователя, если он не найден
                new_user = TgUser(
                    tg_id=user_data["tg_id"],
                    name=user_data["name"],
                    username=user_data["username"],
                    phone=user_data["phone"],
                    surname="",
                    registration_date=datetime.now(),
                )
                session.add(new_user)

            # Фиксируем изменения в базе данных
            await session.commit()
    return True


async def get_all_users():
    async with async_session_maker() as session:
        query = select(TgUser).filter(
            not_(TgUser.permissions.in_([UserPermissions.admin, UserPermissions.superadmin]))
        )
        result = await session.execute(query)
        users = result.scalars().all()
        return users


async def create_message(text: str):
    async with async_session_maker() as session:
        new_message = Message(
            name=text,
            text=text,
        )
        session.add(new_message)
        await session.commit()
        await session.refresh(new_message)
        return new_message


async def get_message_to_mailing_by_id(message_id: int):
    async with async_session_maker() as session:
        query = select(Message).filter_by(id=message_id)
        result = await session.execute(query)
        message = result.scalars().first()
        return message


async def create_mailing(text, user, description=None):
    if isinstance(text, int):
        message_id = int(text)
        message = await get_message_to_mailing_by_id(message_id)
    else:
        message = await create_message(text)

    async with async_session_maker() as session:
        new_mailing = Mailing(
            name=text,
            description=description,
            creator=user.id,
            status=MailingStatus.DRAFT,
            message_id=message.id,
        )
        session.add(new_mailing)
        await session.commit()
        await session.refresh(new_mailing)
        return new_mailing


async def get_logs_from_mailing_by_message_id(message_id):

    time_boundary = datetime.now() - timedelta(minutes=10)

    async with async_session_maker() as session:
        query = select(MessageLog).where(
            MessageLog.message_id == message_id,
            MessageLog.timestamp >= time_boundary
        )
        result = await session.execute(query)
        logs = result.scalars().all()
        return logs


async def get_message_by_mailing_id(mailing_id):
    async with async_session_maker() as session:
        result = await session.execute(
            select(Mailing).where(Mailing.id == mailing_id).options(joinedload(Mailing.message))
        )
        mailing = result.scalars().first()

        # Проверка наличия рассылки и связанного с ней сообщения
        if mailing and mailing.message:
            return mailing.message
        else:
            return None


async def get_mailing_logs_ids(mailing_message_id):
    async with async_session_maker() as session:
        if mailing_message_id:
            logs_result = await session.execute(
                select(MessageLog)
                .where(MessageLog.message_id == mailing_message_id)
                .options(joinedload(MessageLog.user))  # Загружаем связанные объекты User
            )
            logs = logs_result.scalars().all()
            return logs
        else:
            return None


