import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

import requests
import telegram
from dotenv import load_dotenv

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
    except Exception as error:
        logger.error(f'Ошибка при отправке сообщения!: {error}')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp}
                                )
    except Exception as error:
        msg = f'Ошибка при запросе к эндпоинту: {error}'
        logger.error(msg)
        raise APIAnswerException(msg)

    if response.status_code != HTTPStatus.OK:
        msg = f'Эндпоинт не доступен, код HTTP: {response.status_code}'
        logger.error(msg)
        raise HTTPStatusNot200(msg)
    else:
        logger.info('Получен ответ от API.')
        return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        msg = f'Тип ответа API - не словарь: {response}'
        logger.error(msg)
        raise TypeError(msg)
    if 'homeworks' not in response:
        msg = f'Отсутствует ключ homeworks в ответе API: {response}'
        logging.error(msg)
        raise KeyError(msg)
    if not isinstance(response['homeworks'], list):
        msg = f'Значение ключа homeworks приходит не в виде списка: {response}'
        logging.error(msg)
        raise TypeError(msg)
    homeworks = response['homeworks']
    return homeworks


def parse_status(homework):
    """Извлечение статуса домашней работы."""
    if 'homework_name' not in homework:
        msg = 'В ответе API домашнего задания нет ключа homework_name.'
        logger.error(msg)
        raise KeyError(msg)
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        msg = 'В ответе от API получен неожиданный статус домашней работы.'
        logger.error(msg)
        raise NotValidStatus(msg)
    else:
        logger.info('Получен статус домашней работы.')
        verdict = HOMEWORK_VERDICTS[status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    logger.info('Yandex Practicum HW bot запущен в работу.')
    previous_message = None
    while True:
        try:
            logger.info('Отправка запроса к API.')
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logger.info('Нет задания на проверке.')
                continue
            current_message = parse_status(homeworks[0])
            if current_message != previous_message:
                send_message(bot, current_message)
                previous_message = current_message
                timestamp = response['current_date']
            else:
                logger.info('Статус проверки работы не изменился.')
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
