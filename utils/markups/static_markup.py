from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from typing import List, Optional


async def reply_markup(btns: List[str]) -> Optional[ReplyKeyboardMarkup]:

    if not btns:
        return None  # Возвращаем None, если список кнопок пуст

    keyboard = []
    for btn in btns:
        keyboard.append([KeyboardButton(text=btn)])

    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)
    return markup
