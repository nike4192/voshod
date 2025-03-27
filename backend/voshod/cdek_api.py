import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class CDEKApi:
    def __init__(self, client_id=None, client_secret=None, base_url='https://api.edu.cdek.ru'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.token = None
        self.token_expires = None

    def get_auth_token(self):
        """Получение JWT токена для авторизации в API CDEK"""
        url = f"{self.base_url}/v2/oauth/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        try:
            response = requests.post(url, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.token = token_data.get('access_token')
            # Устанавливаем время жизни токена
            self.token_expires = datetime.now().timestamp() + token_data.get('expires_in', 3600)

            return self.token
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting CDEK auth token: {e}")
            return None

    def ensure_token(self):
        """Проверяет наличие и актуальность токена"""
        current_time = datetime.now().timestamp()

        if not self.token or not self.token_expires or current_time >= self.token_expires:
            return self.get_auth_token()

        return self.token

    def calculate_shipping(self, postal_code, weight, length=2, width=2, height=1000):
        """
        Расчет стоимости доставки CDEK

        Args:
            postal_code: Почтовый индекс получателя
            weight: Вес посылки в граммах
            length, width, height: Размеры посылки в см

        Returns:
            dict: Информация о стоимости доставки
        """
        token = self.ensure_token()

        if not token:
            return {"error": "Failed to get CDEK authentication token"}

        url = f"{self.base_url}/v2/calculator/tarifflist"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "date": "",
            "type": 1,
            "lang": "rus",
            "from_location": {
                "postal_code": "119071",
                "country_code": "RU",
                "contragent_type": "LEGAL_ENTITY"
            },
            "to_location": {
                "postal_code": postal_code,
                "country_code": "RU",
                "contragent_type": "INDIVIDUAL"
            },
            "packages": [
                {
                    "weight": weight,
                    "length": length,
                    "width": width,
                    "height": height
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            result = response.json()

            # Ищем тариф с кодом 482 (Экспресс склад-дверь)
            shipping_cost = None

            for tariff in result.get("tariff_codes", []):
                if tariff.get("tariff_code") == 482:
                    shipping_cost = tariff.get("delivery_sum")
                    break

            if shipping_cost is None:
                return {"error": "Tariff code 482 not found in CDEK response"}

            return {
                "status": "success",
                "shipping_cost": shipping_cost,
                "full_response": result  # Можно убрать в продакшене
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calculating CDEK shipping: {e}")
            return {"error": f"CDEK API request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing CDEK response: {e}")
            return {"error": "Failed to parse CDEK API response"}