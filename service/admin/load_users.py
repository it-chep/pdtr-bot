import os
import csv
from datetime import datetime
from aiogram import types
from repository.admin.repository import save_user_to_db


def mime_type_to_extension(mime_type):
    """ Функция для определения расширения файла по его MIME-тип """
    mime_map = {
        'application/pdf': 'pdf',
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'text/plain': 'txt',
        'text/csv': 'csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
    }
    return mime_map.get(mime_type, 'bin')


async def load_users_from_file(message: types.Message) -> bool:
    extension = mime_type_to_extension(message.document.mime_type)
    file_path = os.path.join(
        config.BASE_DIR, 'tg_documents', f"users_load_{datetime.now().strftime('%Y_%m_%d_%H:%M:%S')}.{extension}"
    )
    await message.bot.download(message.document, file_path)

    async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='replace') as f:
        content = await f.read()

    if extension == 'csv':
        return await load_users_csv(content)
    elif extension == 'xlsx':
        return False


async def load_users_csv(content) -> bool:
    reader = csv.reader(content.splitlines())
    for row in reader:
        if len(row) == 1:
            # Скорее всего первая строка
            continue

        big_string = ''.join(row)
        split_data = big_string.split(';')
        if len(split_data) < 10:
            continue

        phone, username = None, None
        for item in split_data:
            # Берем только российский номер телефона
            if not phone and (item.startswith('7') or item.startswith('8') or item.startswith('+7')) and (
                    len(item) in [11, 12]):
                phone = item
            if not username and item.startswith('@'):
                username = item
            if phone and username:
                break

        try:
            user_data = {
                "tg_id": int(split_data[4]),
                "name": split_data[1],
                "username": username,
                "phone": phone
            }
        except ValueError:
            continue
        await save_user_to_db(user_data)

    return True