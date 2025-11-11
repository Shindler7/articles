"""
Учебный модуль. Получение данных через API по погоде.
"""
import asyncio
from json import JSONDecodeError
from typing import Any, Optional

from httpx import AsyncClient, HTTPError

CITY_COORD: dict[str, tuple[float, float]] = {
    "moscow": (55.751244, 37.618423)
}

URL_API_OPEN_METEO: str = 'https://api.open-meteo.com/v1/forecast'
# Набор данных по-умолчанию: температура, влажность, давление.
PARAM_CURRENT_DEFAULT: tuple[tuple[str, str], ...] = (
    ('temperature_2m', 'температура'),
    ('relative_humidity_2m', 'влажность'),
    ('pressure_msl', 'давление')
)


async def weather(city: str, interval_sec: int = 5,
                  param_current: Optional[tuple[tuple[str, str], ...]] = None):
    """
    Организатор запросов к API для получения информации о погоде в выбранном
    городе.

    :param city: Название города проверки погоды.
    :param interval_sec: Частота запросов к API.
    :param param_current: Набор запрашиваемых данных. Если не указано, берётся
                          стандартный набор.
    """

    city = city.lower()  # Делаем буквы строчными, исключая разницу регистров.
    if param_current is None:
        # Берём данные по-умолчанию, если они не переданы при вызове функции.
        param_current = PARAM_CURRENT_DEFAULT

    # Проверка, что координаты запрошенного города есть в базе.
    if CITY_COORD.get(city) is None:
        raise KeyError(f'Отсутствуют данные по данному городу: {city}')

    client = AsyncClient()  # Создали экземпляр клиента для запросов к API.

    while True:
        """
        В этом цикле с заданным интервалом делается запрос к функции, которая
        получает данные через API и возвращает их в словаре.
        """
        data_weather: dict[str, Any] = await fetch_api(client,
                                                       CITY_COORD[city],
                                                       param_current)

        # Вызываем функцию, которая выводит данные в консоль.
        print_weather(city.capitalize(), data_weather, param_current)

        await asyncio.sleep(interval_sec)  # Пауза между запросами.


async def fetch_api(client: AsyncClient,
                    city_coord: tuple[float, float],
                    param_current: tuple[tuple[str, str], ...]) -> dict[
    str, Any]:
    """
    Совершить запрос к API и гарантированно вернуть данные.

    Если будут возникать ошибки доступа к сайту, будет совершено 5 попыток,
    после этого программа завершиться аварийно, если ситуация не улучшится.

    :param client: Экземпляр AsyncClient.
    :param city_coord: Координаты города проверки погоды. Кортеж с двумя float.
    :param param_current: Набор запрашиваемых данных.
    :return: Словарь с данными успешного запроса.
    """

    # Задаём параметры запроса, согласно документации API.
    params = {
        'latitude': city_coord[0],
        'longitude': city_coord[1],
        'current': ','.join(d[0] for d in param_current),
    }
    repeat_fetch = 0
    while repeat_fetch < 5:
        """ Цикл выполнится 5 раз, если хоть 1 запрос будет успешным, то его
        исполнение прервётся. """

        # Запрос к API.
        response = await client.get(URL_API_OPEN_METEO, params=params)

        # Совершаем запрос в блоке проверки исключений (ошибок).
        try:
            response.raise_for_status()
            data = response.json()
            return data  # Если данные получены, здесь выход с ними.
        except HTTPError as e:
            print(f'Ошибка: {e}')
        except JSONDecodeError as e:
            print(f'Ошибка: {e.msg}')

        await asyncio.sleep(3)
        repeat_fetch += 1

    raise ValueError('Данные для data_weather отсутствуют.')


def print_weather(city_name: str,
                  data_weather: dict[str, Any],
                  param_current: tuple[tuple[str, str], ...]):
    """
    Вывести в консоль данные о погоде.

    :param city_name: Название города (как передано, так и выведено).
    :param data_weather: Данные в словаре с информацией о погоде.
    :param param_current: Набор запрошенных данных.
    """

    units = 'current_units'
    current = 'current'

    # Проверяем, что есть ключевые блоки в полученных данных.
    if data_weather.get(current) is None or data_weather.get(units) is None:
        raise KeyError('Неверный состав полученных от API данных.')

    data = data_weather[current]
    data_units = data_weather[units]

    # Выводим информацию в консоль.
    print(f'\nПогода в городе {city_name}')
    for param in param_current:
        param_key, param_title = param

        try:
            print(f'{param_title.capitalize()}: '
                  f'{data_weather[current][param_key]} '
                  f'{data_weather[units][param_key]}')
        except KeyError as e:
            print(f'Ошибка: данные "{param_key}" отсутствуют или неполные.')
