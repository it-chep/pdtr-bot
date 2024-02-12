from typing import List, Optional

from aiogram.types import (
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import models
from config import ButtonsConfig


async def inline_markup(btns: List[models.MessageButton]) -> Optional[InlineKeyboardMarkup]:
    if not btns:
        return None  # Возвращаем None, если список кнопок пуст
    markup = []
    for btn in btns:
        if btn.action_type_id == int(ButtonsConfig.URL_BUTTON.value):
            markup.append([InlineKeyboardButton(text=btn.text, url=btn.button_action)])
        elif btn.action_type_id == int(ButtonsConfig.WEB_APP_BUTTON.value):
            markup.append([InlineKeyboardButton(text=btn.text, web_app=btn.button_action)])
        else:
            markup.append([InlineKeyboardButton(text=btn.text, callback_data=btn.button_action)])
    markup = InlineKeyboardMarkup(inline_keyboard=markup)
    return markup


async def reply_markup(btns: List[models.MessageButton]) -> Optional[ReplyKeyboardMarkup]:
    if not btns:
        return None  # Возвращаем None, если список кнопок пуст

    keyboard = []
    for btn in btns:
        if btn.action_type_id == int(ButtonsConfig.PHONE_BUTTON.value):
            keyboard.append([KeyboardButton(text=btn.text, request_contact=True)])
        elif btn.action_type_id == int(ButtonsConfig.GEO_BUTTON.value):
            keyboard.append([KeyboardButton(text=btn.text, request_location=True)])
        else:
            keyboard.append([KeyboardButton(text=btn.text)])

    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)
    return markup


async def build_markup(btns: List[models.MessageButton], button_type_id: int = 0):
    if button_type_id == int(ButtonsConfig.CALLBACK_BUTTON.value):
        return await inline_markup(btns)
    else:
        return await reply_markup(btns)


async def clean_markup():
    return ReplyKeyboardRemove()
