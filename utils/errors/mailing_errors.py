
class StepNotFoundError(Exception):
    def __init__(self, text="Step not found"):
        self.text = text
        super(StepNotFoundError).__init__(self.text)