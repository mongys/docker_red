from pydantic import BaseModel

class UserCreateModel(BaseModel):
    username: str
    password: str

class TokenModel(BaseModel):
    access_token: str
    token_type: str

class UserResponseModel(BaseModel):
    username: str

class ContainerInfoModel(BaseModel):
    id: str
    name: str
    status: str
    image: str

class ContainerActionRequest(BaseModel):
    container_id: str

class CloneAndRunRequest(BaseModel):
    github_url: str
    dockerfile_dir: str = ""

class ContainerStatsModel(BaseModel):
    cpu_usage: float
    system_cpu_usage: float
    memory_usage: int
    memory_limit: int
    network_io: dict

