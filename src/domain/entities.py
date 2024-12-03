from pydantic import BaseModel
from dataclasses import dataclass

class User(BaseModel):
    username: str
    hashed_password: str

@dataclass
class Container:
    id: str
    name: str
    status: str
    image: str
    is_in_db: bool = False 
