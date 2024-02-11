import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE = os.getenv("DATABASE")
DEFAULT_TIMEOUT = 60 * 60
BROKER_URL = os.getenv("BROKER_URL")


# TODO: красиво сделать
class ButtonsConfig(Enum):
    """
        Enumeration for different types of buttons used in the application.

        Attributes:
            DEFAULT_BUTTON: A default button type.
            CALLBACK_BUTTON: A button that triggers a callback.
            GEO_BUTTON: A button to request geolocation.
            PHONE_BUTTON: A button to request a phone number.
            URL_BUTTON: A button that redirects to a URL.
            WEB_APP_BUTTON: A button that opens a web application.
        """
    DEFAULT_BUTTON = "1"
    CALLBACK_BUTTON = "2"
    GEO_BUTTON = "4"
    PHONE_BUTTON = "3"
    URL_BUTTON = "5"
    WEB_APP_BUTTON = "6"


# TODO: сделать dict для разных загрузок по типу
"""
AcceptableFormats = {
    "upload_users": ['text/csv', 'text/html'],
    "upload_questions": ['text/csv', 'text/html'],
    "upload_messages": ['text/csv', 'text']
}
"""
AcceptableFormats = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', ]


BASE_DIR = os.path.dirname(os.path.abspath(__file__))