import logging
import os
import sys
import time
from http import HTTPStatus
from json.decoder import JSONDecodeError
from logging import StreamHandler

import requests
import telegram
from dotenv import load_dotenv
from requests import (ConnectionError, HTTPError, RequestException, Timeout,
                      TooManyRedirects)
from telegram import TelegramError

from exceptions import APIAnswerException, HTTPStatusNot200, NotValidStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    if not all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        logger.critical('Отсутствуют обязательные переменные окружения!')
        sys.exit()


def send_message(bot, message):
    """Отправка сообщения в Telegram в чат c id=TELEGRAM_CHAT_ID."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Сообщение отправлено в чат с id: {TELEGRAM_CHAT_ID}.')
    except TelegramError as error:
        logger.error(f'Ошибка при отправке сообщения!: {error}')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp}
                                )
    except HTTPError as error:
        msg = f'Ошибка HTTP: {error}'
        raise HTTPError(msg)
    except ConnectionError as error:
        msg = f'Ошибка соединения: {error}'
        raise ConnectionError(msg)
    except Timeout as error:
        msg = f'Ошибка тайм-аута: {error}'
        raise Timeout(msg)
    except TooManyRedirects as error:
        msg = f'Ошибка множественных редиректов: {error}'
        raise TooManyRedirects(msg)
    except RequestException as error:
        msg = f'Ошибка при запросе к эндпоинту: {error}'
        raise APIAnswerException(msg)
    if response.status_code != HTTPStatus.OK:
        msg = f'Эндпоинт не доступен, код HTTP: {response.status_code}'
        raise HTTPStatusNot200(msg)
    logger.info('Получен ответ от API.')
    try:
        return response.json()
    except JSONDecodeError as error:
        msg = f'Ошибка форматирования в JSON: {error}'
        raise JSONDecodeError(msg)


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        msg = f'Тип ответа API - не словарь: {response}'
        raise TypeError(msg)
    if 'current_date' not in response:
        msg = f'Отсутствует ключ current_date в ответе API: {response}'
        raise KeyError(msg)
    if not isinstance(response['current_date'], int):
        msg = f'Значение ключа current_date не целое число: {response}'
        raise TypeError(msg)
    if 'homeworks' not in response:
        msg = f'Отсутствует ключ homeworks в ответе API: {response}'
        raise KeyError(msg)
    if not isinstance(response['homeworks'], list):
        msg = f'Значение ключа homeworks приходит не в виде списка: {response}'
        raise TypeError(msg)
    homeworks = response['homeworks']
    return homeworks


def parse_status(homework):
    """Извлечение статуса домашней работы."""
    if 'homework_name' not in homework:
        msg = 'В ответе API домашнего задания нет ключа homework_name.'
        raise KeyError(msg)
    homework_name = homework['homework_name']
    try:
        status = homework['status']
    except KeyError as error:
        msg = f'Отсутствует ключ status: {error}'
        raise KeyError(msg)
    if status not in HOMEWORK_VERDICTS:
        msg = 'В ответе от API получен неожиданный статус домашней работы.'
        raise NotValidStatus(msg)
    logger.info('Получен статус домашней работы.')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    logger.info('Yandex Practicum HW bot запущен в работу.')
    while True:
        try:
            logger.info('Отправка запроса к API.')
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                send_message(bot, message)
                timestamp = response['current_date']
            else:
                logger.info('Нет новых статусов.')
        except Exception as error:
            logger.error(f'Сбой в работе программы: {error}')
        finally:
            logger.info(f'Ожидание {RETRY_PERIOD} с. перед отправкой запроса.')
            time.sleep(RETRY_PERIOD)


logging.basicConfig(
    level=logging.DEBUG,
    filename='logging.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

if __name__ == '__main__':
    main()
