"""
Модуль проекта о погоде
"""
import asyncio
from core import weather


def main():

    city = 'moscow'

    asyncio.run(weather.weather(city))


if __name__ == '__main__':
    main()
