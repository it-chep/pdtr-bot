class ConditionNotFoundError(Exception):
    def __init__(self, text="Условие не найдено"):
        self.text = text
        super(ConditionNotFoundError, self).__init__(self.text)


class MessageNotFoundError(Exception):
    def __init__(self, text="Сообщение не найдено"):
        self.text = text
        super(MessageNotFoundError, self).__init__(self.text)
