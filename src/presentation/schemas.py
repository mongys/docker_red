from pydantic import BaseModel, Field

class UserCreateModel(BaseModel):
    username: str = Field(..., title="Username", description="The unique username of the user.", min_length=3, max_length=30)
    password: str = Field(..., title="Password", description="The password for the user. Should be secure.", min_length=8)

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123!"
            }
        }

class TokenModel(BaseModel):
    access_token: str = Field(..., title="Access Token", description="The token used for authenticating requests.")
    token_type: str = Field(..., title="Token Type", description="The type of the token, usually 'bearer'.")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
                "token_type": "bearer"
            }
        }

class UserResponseModel(BaseModel):
    username: str = Field(..., title="Username", description="The unique username of the user.")

    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe"
            }
        }

class ContainerInfoModel(BaseModel):
    id: str = Field(..., title="Container ID", description="The unique identifier of the Docker container.")
    name: str = Field(..., title="Container Name", description="The name of the Docker container.")
    status: str = Field(..., title="Container Status", description="The current status of the Docker container (e.g., running, exited).")
    image: str = Field(..., title="Image", description="The Docker image used by the container.")

    class Config:
        schema_extra = {
            "example": {
                "id": "e4c88bf1725a98abc...",
                "name": "web_app",
                "status": "running",
                "image": "nginx:latest"
            }
        }

class ContainerActionRequest(BaseModel):
    container_id: str = Field(..., title="Container ID", description="The unique identifier of the Docker container.")

    class Config:
        schema_extra = {
            "example": {
                "container_id": "e4c88bf1725a98abc..."
            }
        }

class CloneAndRunRequest(BaseModel):
    github_url: str = Field(..., title="GitHub URL", description="The URL of the GitHub repository to clone.")
    dockerfile_dir: str = Field("", title="Dockerfile Directory", description="The directory in the repository containing the Dockerfile.")

    class Config:
        schema_extra = {
            "example": {
                "github_url": "https://github.com/example/repo.git",
                "dockerfile_dir": "/docker"
            }
        }

class ContainerStatsModel(BaseModel):
    cpu_usage: float = Field(..., title="CPU Usage", description="The percentage of CPU usage by the container.")
    system_cpu_usage: float = Field(..., title="System CPU Usage", description="The total CPU usage of the system.")
    memory_usage: int = Field(..., title="Memory Usage", description="The memory usage of the container in bytes.")
    memory_limit: int = Field(..., title="Memory Limit", description="The memory limit of the container in bytes.")
    network_io: dict = Field(..., title="Network IO", description="The network input/output statistics of the container.")

    class Config:
        schema_extra = {
            "example": {
                "cpu_usage": 2.5,
                "system_cpu_usage": 50.0,
                "memory_usage": 1048576,
                "memory_limit": 2097152,
                "network_io": {
                    "received": {"bytes": "1.0 MB", "packets": 120},
                    "transmitted": {"bytes": "0.5 MB", "packets": 80}
                }
            }
        }
