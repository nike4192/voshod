import requests
import json
import logging
import traceback

logger = logging.getLogger(__name__)


class PochtaAPI:
    def __init__(self, token, key):
        logger.debug(f"Initializing PochtaAPI with token: {token[:5]}... and key: {key[:5]}...")
        self.token = token
        self.key = key
        self.base_url = "https://otpravka-api.pochta.ru"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json;charset=UTF-8",
            "Authorization": f"AccessToken {token}",
            "X-User-Authorization": f"Basic {key}"
        }
        logger.debug(f"Headers: {self.headers}")

    def normalize_address(self, address):
        """
        Нормализация адреса через API Почты России

        :param address: Строка с адресом или список адресов для нормализации
        :return: Результат нормализации адреса
        """
        logger.debug(f"normalize_address called with address: {address}")
        url = f"{self.base_url}/1.0/clean/address"
        logger.debug(f"API URL: {url}")

        try:
            # Преобразуем одиночный адрес в список для унификации обработки
            if isinstance(address, str):
                addresses = [{"id": "1", "original-address": address}]
            else:
                addresses = [{"id": str(i + 1), "original-address": addr} for i, addr in enumerate(address)]

            logger.debug(f"Prepared addresses: {addresses}")

            # Преобразуем в JSON для логирования
            json_data = json.dumps(addresses, ensure_ascii=False)
            logger.debug(f"JSON data: {json_data}")

            # Отправляем запрос
            logger.debug("Sending POST request to Pochta API")
            response = requests.post(
                url,
                headers=self.headers,
                json=addresses,
                timeout=60
            )

            # Логируем ответ
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            # Проверяем статус ответа
            if response.status_code != 200:
                logger.error(f"Error response: {response.text}")
                return {"error": f"API returned status {response.status_code}: {response.text}"}

            # Парсим JSON-ответ
            try:
                result = response.json()
                logger.debug(f"Parsed JSON response: {result}")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON response: {e}")
                logger.error(f"Response text: {response.text}")
                return {"error": f"Invalid JSON response: {str(e)}"}

            # Если был передан один адрес, возвращаем только его результат
            if isinstance(address, str):
                logger.debug("Returning single address result")
                return result[0] if result else None

            logger.debug("Returning multiple addresses result")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Unexpected error: {str(e)}"}

    def calculate_shipping(self, index_to, mass, height=2, length=5, width=197, mail_category="ORDINARY",
                           mail_type="POSTAL_PARCEL", fragile=True):
        """
        Расчет стоимости доставки через API Почты России

        Параметры:
        - index_to: индекс получателя (получается при нормализации адреса)
        - mass: вес отправления в граммах
        - height: высота (см)
        - length: длина (см)
        - width: ширина (см)
        - mail_category: категория отправления (по умолчанию "ORDINARY")
        - mail_type: тип отправления (по умолчанию "POSTAL_PARCEL")
        - fragile: хрупкое отправление (по умолчанию True)

        Возвращает:
        - результат расчета стоимости доставки или словарь с ошибкой
        """
        try:
            logger.debug(f"Calculating shipping cost to index: {index_to}, mass: {mass}g")

            url = f"{self.base_url}/1.0/tariff"

            payload = {
                "index-to": index_to,
                "mail-category": mail_category,
                "mail-type": mail_type,
                "mass": mass,
                "dimension": {
                    "height": height,
                    "length": length,
                    "width": width
                },
                "fragile": str(fragile).lower()
            }

            logger.debug(f"Request payload: {payload}")

            # Отправляем запрос
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=60
            )

            # Логируем ответ
            logger.debug(f"Response status code: {response.status_code}")

            # Проверяем статус ответа
            if response.status_code != 200:
                logger.error(f"Error response: {response.text}")
                return {"error": f"API returned status {response.status_code}: {response.text}"}

            # Парсим и возвращаем результат
            result = response.json()
            logger.debug(f"Shipping calculation result: {result}")

            # Извлекаем стоимость доставки из ответа
            # Судя по примеру ответа, стоимость доставки находится в поле total-rate
            if "total-rate" in result:
                # total-rate в копейках, переводим в рубли
                cost_in_rubles = result["total-rate"] / 100
                logger.debug(
                    f"Extracted shipping cost from total-rate: {result['total-rate']} kopecks = {cost_in_rubles} rubles")
                result["cost_in_rubles"] = cost_in_rubles
            else:
                # Если поле total-rate отсутствует, проверяем другие возможные поля
                if "ground-rate" in result and "rate" in result["ground-rate"]:
                    # ground-rate.rate в копейках, переводим в рубли
                    cost_in_rubles = result["ground-rate"]["rate"] / 100
                    logger.debug(
                        f"Extracted shipping cost from ground-rate.rate: {result['ground-rate']['rate']} kopecks = {cost_in_rubles} rubles")
                    result["cost_in_rubles"] = cost_in_rubles
                elif "fragile-rate" in result and "rate" in result["fragile-rate"]:
                    # fragile-rate.rate в копейках, переводим в рубли
                    cost_in_rubles = result["fragile-rate"]["rate"] / 100
                    logger.debug(
                        f"Extracted shipping cost from fragile-rate.rate: {result['fragile-rate']['rate']} kopecks = {cost_in_rubles} rubles")
                    result["cost_in_rubles"] = cost_in_rubles
                else:
                    # Если не нашли ни одного из известных полей, устанавливаем стоимость по умолчанию
                    logger.warning("Could not find shipping cost in API response, using default value")
                    result["cost_in_rubles"] = 300

            return result

        except Exception as e:
            error_message = f"Error calculating shipping cost: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            return {"error": error_message}

class AddressValidator:
    def _is_valid_quality(self, quality_code):
        """
        Проверка, является ли код качества допустимым для использования
        """
        valid_codes = ['GOOD', 'POSTAL_BOX', 'ON_DEMAND', 'ACCURATE']
        return quality_code in valid_codes

    def _get_quality_description(self, quality_code):
        """
        Получение описания кода качества нормализации
        """
        quality_descriptions = {
            'GOOD': 'Все элементы адреса распознаны уверенно',
            'POSTAL_BOX': 'Почтовый ящик',
            'ON_DEMAND': 'До востребования',
            'UNDEF_05': 'Неоднозначность, связанная с регионами',
            'UNDEF_01': 'Неоднозначность, связанная с районами',
            'UNDEF_02': 'Неоднозначность, связанная с городами',
            'UNDEF_03': 'Неоднозначность, связанная с населенными пунктами',
            'UNDEF_04': 'Неоднозначность, связанная с улицами',
            'UNDEF_06': 'Неоднозначность, связанная с домами',
            'UNDEF_07': 'Иная неоднозначность',
            'INCORRECT': 'Адрес распознан с ошибками',
            'ACCURATE': 'Адрес распознан с предупреждениями',
        }
        return quality_descriptions.get(quality_code, 'Неизвестный код качества')

    def validate_address(self, result):
        """
        Проверка результата нормализации адреса
        """
        if not result:
            return False, "Результат нормализации пуст"

        quality_code = result.get('quality-code', '')
        is_valid = self._is_valid_quality(quality_code)
        quality_description = self._get_quality_description(quality_code)

        if not is_valid:
            return False, f"Недопустимое качество нормализации: {quality_description}"

        return True, quality_description


# @api_view(['POST'])
# def normalize_address(request):
#     """
#     Представление для нормализации адреса
#     """
#     address = request.data.get('address')
#     if not address:
#         return JsonResponse({
#             'status': 'error',
#             'message': 'Address is required'
#         }, status=400)
#
#     # Создаем экземпляры классов
#     pochta_api = PochtaAPI(settings.POCHTA_API_TOKEN, settings.POCHTA_API_KEY)
#     validator = AddressValidator()
#
#     # Вызов API для нормализации адреса
#     result = pochta_api.normalize_address(address)
#
#     if isinstance(result, dict) and 'error' in result:
#         return JsonResponse({
#             'status': 'error',
#             'message': result['error']
#         }, status=400)
#
#     # Проверка качества нормализации
#     is_valid, message = validator.validate_address(result)
#
#     if not is_valid:
#         return JsonResponse({
#             'status': 'error',
#             'message': message
#         }, status=400)
#
#     # Возвращаем успешный результат
#     return JsonResponse({
#         'status': 'success',
#         'normalized_address': result,
#         'quality_description': message
#     })