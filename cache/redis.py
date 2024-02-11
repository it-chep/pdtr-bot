import decimal
import logging
import time
import json
from datetime import datetime
from config import DEFAULT_TIMEOUT

import redis
import config

logger = logging.getLogger(__name__)


class RedisClient(object):

    def __init__(self):
        super().__init__()
        self.client = self.get_redis_client()

    def get_redis_client(self, broker_url=None):
        try:
            client = self.get_redis(broker_url)
            client.echo("test")
        except (redis.ConnectionError, redis.ResponseError) as e:
            if config.DEBUG or config.TEST_CONFIGURATION:
                client = get_fake_redis()
            else:
                raise redis.ConnectionError("Redis not available: {}".format(e))
        return client

    def get_redis(self, broker_url=None, new_connect=False):
        client = getattr(self, "client", None)
        if client and new_connect:
            client = None
        if client is None:
            pool = redis.ConnectionPool.from_url(broker_url or config.BROKER_URL)
            client = redis.Redis(connection_pool=pool)
            self.client = client
        return client

    def get_user_state(self, user_id):
        """
        Получить состояние пользователя из Redis.
        """
        try:
            state = self.client.get(user_id)
            return state.decode('utf-8') if state else None
        except redis.RedisError as e:
            print(f"Ошибка при получении состояния пользователя: {e}")
            return None

    def get(self, key):
        """
        Получить значение по ключу из Redis.
        """
        try:
            state = self.client.get(key)
            return state.decode('utf-8') if state else None
        except redis.RedisError as e:
            print(f"Ошибка при получении значения {e}")
            return None

    def set_user_state(self, user_id, state):
        """
        Установить новое состояние пользователя в Redis.
        """
        try:
            self.client.set(user_id, state)
            return True
        except redis.RedisError as e:
            print(f"Ошибка при установке состояния пользователя: {e}")
        return False

    def set(self, key, value):
        """
        Установить новое состояние пользователя в Redis.
        """
        try:
            self.client.set(key, value)
            return True
        except redis.RedisError as e:
            print(f"Ошибка при установке значения {e}")
        return False

    def keys(self, key_pattern):
        keys = self.client.keys(key_pattern)
        keys_decoded = [key.decode('utf-8') for key in keys]
        return keys_decoded

    def get_last_draft(self, user_id):
        key_pattern = f"mailing_draft:{user_id}:*"
        keys = self.keys(key_pattern)
        if keys:
            last_draft_key = max(keys, key=lambda k: k.split(":")[-1])
            draft_json = self.get(last_draft_key)
            return last_draft_key, json.loads(draft_json)
        return None, None

    def delete_user_state(self, user_id):
        """
            Удалить состояние пользователя из Redis.
            :param user_id: Уникальный идентификатор пользователя
            :return: True, если состояние было удалено, False в случае ошибки
            """
        try:
            result = self.client.delete(user_id)
            return result == 1  # Возвращает True, если ключ был найден и удален
        except redis.RedisError as e:
            print(f"Ошибка при удалении состояния пользователя: {e}")
            return False

    def delete(self, key):
        """
            Удалить состояние пользователя из Redis.
            :param key:
            :return: True, если состояние было удалено, False в случае ошибки
            """
        try:
            result = self.client.delete(key)
            return result == 1  # Возвращает True, если ключ был найден и удален
        except redis.RedisError as e:
            print(f"Ошибка при удалении ключа: {e}")
            return False


redis_client = RedisClient()


class FakeRedis(object):
    def get(self, key):
        return getattr(self, key, None)

    def keys(self, pattern="*"):
        if pattern != "*":
            pattern = pattern.replace("*", "")
            return [key for key in self.__dict__.keys() if pattern in key]
        else:
            return list(self.__dict__.keys())

    def hget(self, name, key):
        return str(hash(name + key))

    def set(self, key, value, *args, **kwargs):
        setattr(self, key, value)

    def setex(self, key, timeout, value):
        setattr(self, key, value)

    def exists(self, key):
        return hasattr(self, key)

    def delete(self, key):
        if self.exists(key):
            return delattr(self, key)

    def flushdb(self):
        pass


def get_fake_redis():
    return FakeRedis()
