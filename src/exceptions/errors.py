class PasswordOrLoginExc(Exception):
    """Ошибка валидации пароли или логина"""

    pass


class UnauthorizedExc(Exception):
    """Ошибка аутентификации"""

    def __init__(self, detail: str):
        self.detail = detail
