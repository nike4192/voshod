import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import logging

logger = logging.getLogger(__name__)


class PochtaAPI:
    def __init__(self, token, key):
        self.base_url = "https://otpravka-api.pochta.ru"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json;charset=UTF-8",
            "Authorization": f"AccessToken {token}",
            "X-User-Authorization": f"Basic {key}"
        }

    def normalize_address(self, address):
        """
        Нормализация адреса через API Почты России

        :param address: Строка с адресом или список адресов для нормализации
        :return: Результат нормализации адреса
        """
        url = f"{self.base_url}/1.0/clean/address"

        # Преобразуем одиночный адрес в список для унификации обработки
        if isinstance(address, str):
            addresses = [{"id": "1", "original-address": address}]
        else:
            addresses = [{"id": str(i + 1), "original-address": addr} for i, addr in enumerate(address)]

        try:
            logger.info(f"Normalizing addresses: {addresses}")

            # Отключаем проверку SSL-сертификата (только для отладки!)
            # В продакшене этого делать НЕ рекомендуется!
            response = requests.post(
                url,
                headers=self.headers,
                json=addresses,
                timeout=60,  # Увеличиваем таймаут до 60 секунд
                verify=False  # Отключаем проверку SSL (только для отладки!)
            )

            # Логирование ответа для отладки
            logger.info(f"Response status code: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"Error response: {response.text}")

            response.raise_for_status()  # Проверка на ошибки HTTP

            result = response.json()
            logger.info(f"Normalized addresses: {result}")

            # Если был передан один адрес, возвращаем только его результат
            if isinstance(address, str):
                return result[0] if result else None

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error normalizing address: {e}", exc_info=True)
            return {"error": str(e)}