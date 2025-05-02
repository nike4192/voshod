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

    def calculate_shipping(self, city, address, weight, length=2, width=2, height=1000):
        """
        Расчет стоимости доставки CDEK по названию города и адресу

        Args:
            city (str): Название города (не код)
            address (str): Адрес пункта выдачи
            weight (int): Вес отправления в граммах
            length (int): Длина отправления в см
            width (int): Ширина отправления в см
            height (int): Высота отправления в см

        Returns:
            dict: Результат расчета доставки или информация об ошибке
        """
        # Убедимся, что у нас есть действующий токен
        token = self.ensure_token()
        if not token:
            return {"status": "error", "message": "Failed to get CDEK auth token"}

        # Сначала найдем код города по его названию
        city_result = self.suggest_cities(city)

        if "error" in city_result:
            return {"status": "error", "message": f"Failed to find city: {city_result['error']}"}

        if not city_result.get("cities") or len(city_result["cities"]) == 0:
            return {"status": "error", "message": f"City '{city}' not found"}

        # Берем первый найденный город
        city_code = city_result["cities"][0]["code"]

        # Теперь найдем пункт выдачи по адресу
        delivery_points_result = self.get_delivery_points(city_code)

        if "error" in delivery_points_result:
            return {"status": "error", "message": f"Failed to get delivery points: {delivery_points_result['error']}"}

        if not delivery_points_result.get("delivery_points") or len(delivery_points_result["delivery_points"]) == 0:
            return {"status": "error", "message": f"No delivery points found in city '{city}'"}

        # Ищем пункт выдачи по адресу
        pickup_point_code = None
        for point in delivery_points_result["delivery_points"]:
            if address.lower() in point["address"].lower():
                pickup_point_code = point["code"]
                break

        if not pickup_point_code:
            return {"status": "error", "message": f"Delivery point with address '{address}' not found"}

        # Теперь выполняем расчет стоимости доставки
        url = f"{self.base_url}/v2/calculator/tariff"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Формируем данные для запроса
        payload = {
            "tariff_code": 136,  # Код тарифа для самовывоза (136 - посылка склад-склад)
            "from_location": {
                "code": 270  # Код города отправления (например, Москва)
            },
            "to_location": {
                "code": city_code
            },
            "packages": [{
                "weight": weight,
                "length": length,
                "width": width,
                "height": height
            }]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

            # Извлекаем стоимость доставки
            shipping_cost = 0
            if "total_sum" in result:
                shipping_cost = result["total_sum"]

            return {
                "status": "success",
                "shipping_cost": shipping_cost
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calculating CDEK shipping: {e}")
            return {"status": "error", "message": f"Error calculating shipping: {str(e)}"}

    def suggest_cities(self, city_name):
        """
        Поиск городов по названию для автозаполнения

        Args:
            city_name (str): Название города для поиска

        Returns:
            dict: Результат поиска городов или информация об ошибке
        """
        # Убедимся, что у нас есть действующий токен
        token = self.ensure_token()
        if not token:
            return {"error": "Failed to get CDEK auth token"}

        url = f"{self.base_url}/v2/location/suggest/cities"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "country_code": "RU",
            "name": city_name
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()

            return {
                "status": "success",
                "cities": result
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error suggesting CDEK cities: {e}")
            return {"error": f"CDEK API request failed: {str(e)}"}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing CDEK response: {e}")
            return {"error": "Failed to parse CDEK API response"}

    def get_delivery_points(self, city_code):
        """
        Получение списка пунктов выдачи CDEK по коду города

        Args:
            city_code (str): Код города в системе CDEK

        Returns:
            dict: Результат запроса с пунктами выдачи или информацией об ошибке
        """
        # Проверяем наличие токена
        token = self.ensure_token()
        if not token:
            return {"error": "Не удалось получить токен авторизации CDEK"}

        url = f"{self.base_url}/v2/deliverypoints"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {
            "city_code": city_code
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            delivery_points = response.json()

            # Преобразуем данные для удобства использования
            simplified_points = []

            for point in delivery_points:
                # Получаем адрес из местоположения
                address = point.get("location", {}).get("address_full", "")
                if not address:
                    address = point.get("location", {}).get("address", "")

                # Создаем упрощенный объект пункта выдачи
                simplified_point = {
                    "code": point.get("code", ""),
                    "name": point.get("name", ""),
                    "address": address,
                    "work_time": point.get("work_time", ""),
                    "type": point.get("type", ""),
                    "phone": next((p.get("number", "") for p in point.get("phones", []) if "number" in p), "")
                }

                simplified_points.append(simplified_point)

            return {
                "status": "success",
                "delivery_points": simplified_points
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting CDEK delivery points: {e}")
            return {"error": f"Ошибка при получении пунктов выдачи CDEK: {str(e)}"}

    def calculate_tarifflist(self, from_location_code, to_location_code, to_city_name, to_address, weight, length=20,
                             width=20, height=20):
        """
        Расчет стоимости доставки CDEK через tarifflist

        Args:
            from_location_code (int): Код города отправления
            to_location_code (int): Код города назначения
            to_city_name (str): Название города назначения
            to_address (str): Адрес доставки в городе назначения
            weight (int): Вес отправления в граммах
            length (int): Длина отправления в см
            width (int): Ширина отправления в см
            height (int): Высота отправления в см

        Returns:
            dict: Результат расчета доставки или информация об ошибке
        """
        # Убедимся, что у нас есть действующий токен
        token = self.ensure_token()
        if not token:
            return {"error": "Failed to get CDEK auth token"}

        # Логирование для отладки
        logger.info(
            f"Calculating CDEK tarifflist: from_code={from_location_code}, to_code={to_location_code}, to_city={to_city_name}, weight={weight}")

        url = f"{self.base_url}/v2/calculator/tarifflist"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Формируем данные для запроса согласно документации CDEK API
        payload = {
            "from_location": {
                "code": int(from_location_code),
                "country_code": "RU",
                "city": "Москва",
                "address": "ул. Динамовская, 1А, 110а"
            },
            "to_location": {
                "code": int(to_location_code),
                "country_code": "RU",
                "city": to_city_name,
                "address": to_address
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
            # Логирование запроса
            logger.info(f"CDEK API request to tarifflist: {url}, payload: {json.dumps(payload)}")

            response = requests.post(url, headers=headers, json=payload)

            # Логирование ответа
            logger.info(f"CDEK API response status: {response.status_code}")
            logger.info(f"CDEK API response content: {response.text[:500]}")  # Первые 500 символов для краткости

            response.raise_for_status()
            result = response.json()

            # Проверяем наличие ошибок в ответе API
            if "errors" in result and result["errors"]:
                error_msg = "; ".join([error.get("message", "Unknown error") for error in result["errors"]])
                logger.error(f"CDEK API returned errors: {error_msg}")
                return {"error": error_msg}

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calculating CDEK tarifflist: {e}")
            return {"error": f"Error calculating tarifflist: {str(e)}"}