

class BaseCacheClient(ABC):

    @abstractmethod
    def get(self):
        ...

    @abstractmethod
    def set(self):
        ...

    @abstractmethod
    def delete(self):
        ...


class StateClient(BaseCacheClient):

    def get(self):
        ...

    def set(self):
        ...

    def delete(self):
        ...
