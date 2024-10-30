from pydantic import BaseModel

class User(BaseModel):
    """
    Модель пользователя.

    Attributes:
        username (str): Имя пользователя. Должно быть уникальным и не пустым.
        hashed_password (str): Хэшированный пароль пользователя.
    """
    username: str
    hashed_password: str


class Container(BaseModel):
    """
    Модель Docker-контейнера.

    Attributes:
        id (str): Уникальный идентификатор контейнера.
        name (str): Имя контейнера.
        status (str): Текущий статус контейнера (например, "running", "stopped").
        image (str): Имя образа контейнера, из которого он создан.
    """
    id: str
    name: str
    status: str
    image: str
