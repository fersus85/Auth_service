from pydantic import BaseModel


class UserInfoSchema(BaseModel):
    """
    Схема ответа от сервера аутенитификации Yndx
    Описывает информацию о пользователе, полученную через OAuth.
    Поля:
    - first_name: Имя пользователя.
    - last_name: Фамилия пользователя.
    - display_name: Отображаемое имя пользователя.
    - real_name: Настоящее имя пользователя.
    - login: Логин пользователя на Яндексе.
    - old_social_login: Старый логин пользователя в социальной сети.
    - sex: Пол.
    - id: Уникальный идентификатор пользователя Яндекса.
    - client_id: Идентификатор приложения.
    - psuid: Идентификатор авторизованного пользователя в Яндексе.
    """

    first_name: str
    last_name: str
    display_name: str
    real_name: str
    login: str
    old_social_login: str | None = None
    sex: str
    id: str
    client_id: str
    psuid: str
