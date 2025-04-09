import re
from typing import Union


def normalize_phone_number(phone_number: str) -> Union[str, bool]:
    cleaned_number = re.sub(r'\D', '', phone_number)

    # Проверка и приведение к стандартному формату
    if len(cleaned_number) == 11 and cleaned_number.startswith('7'):
        return cleaned_number
    elif len(cleaned_number) == 10 and cleaned_number.startswith('9'):
        return '7' + cleaned_number
    elif len(cleaned_number) == 11 and cleaned_number.startswith('8'):
        return '7' + cleaned_number[1:]
    elif len(cleaned_number) == 12 and cleaned_number.startswith('+7'):
        return cleaned_number[1:]
    else:
        return False
