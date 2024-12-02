from pydantic import BaseModel

class User(BaseModel):
    username: str
    hashed_password: str


class Container(BaseModel):
    id: str
    name: str
    status: str
    image: str
