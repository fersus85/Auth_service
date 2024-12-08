from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field


class ProtoJWT(BaseModel):
    """
    Модель прототипа JWT токенов
    """

    jti: UUID = Field(..., description="UUID токена")
    user_id: UUID = Field(..., description="UUID пользователя")
    iat: int = Field(..., description="Время создания токена в формате epoch")
    exp: int = Field(..., description="Время истечения токена в формате epoch")

    @property
    def issued_at(self) -> datetime:
        return datetime.fromtimestamp(self.iat)

    @property
    def expires_at(self) -> datetime:
        return datetime.fromtimestamp(self.exp)

    @classmethod
    def from_jwt(cls, token: str, secret_key: str) -> Self:
        """
        Создает экземпляр ProtoJWT из JWT токена.

        :param token: JWT токен в виде строки.
        :param secret_key: Секретный ключ для декодирования токена.
        :return: Экземпляр ProtoJWT.
        """
        pass


class AccessJWT(ProtoJWT):
    pass


class RefreshJWT(ProtoJWT):
    pass
