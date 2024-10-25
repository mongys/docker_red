# domain/entities.py

from pydantic import BaseModel



from pydantic import BaseModel

class User(BaseModel):
    username: str
    hashed_password: str


class Container(BaseModel):
    """
    Модель Docker-контейнера.
    """
    id: str
    name: str
    status: str
    image: str
