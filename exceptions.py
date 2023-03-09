class APIAnswerException(Exception):
    """Ошибка при запросе к эндпоинту."""


class HTTPStatusNot200(Exception):
    """Код ответа сервера не равен 200."""


class NotValidStatus(Exception):
    """API возвращает недокументированный статус домашней работы либо
    домашнюю работу без статуса."""
