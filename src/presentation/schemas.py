"""
This module defines Pydantic models for request and response schemas used in the application.

Models include:
- UserCreateModel: Schema for user registration.
- TokenModel: Schema for authentication tokens.
- UserResponseModel: Schema for user response data.
- ContainerInfoModel: Schema for Docker container information.
- ContainerActionRequest: Schema for actions on Docker containers.
- CloneAndRunRequest: Schema for cloning and running a container.
- ContainerStatsModel: Schema for Docker container statistics.
"""

from pydantic import BaseModel, Field


class UserCreateModel(BaseModel):
    """
    Schema for creating a new user.

    Attributes:
        username (str): The unique username of the user.
        password (str): The password for the user. Should meet security requirements.
    """

    username: str = Field(
        ...,
        title="Username",
        description="The unique username of the user.",
        min_length=3,
        max_length=30,
    )
    password: str = Field(
        ...,
        title="Password",
        description="The password for the user. Should be secure.",
        min_length=8,
    )

    class Config:
        schema_extra = {
            "example": {"username": "john_doe", "password": "SecurePass123!"}
        }


class TokenModel(BaseModel):
    """
    Schema for representing authentication tokens.

    Attributes:
        access_token (str): The token used for authenticating requests.
        token_type (str): The type of token, usually 'bearer'.
    """

    access_token: str = Field(
        ...,
        title="Access Token",
        description="The token used for authenticating requests.",
    )
    token_type: str = Field(
        ..., title="Token Type", description="The type of the token, usually 'bearer'."
    )

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
                "token_type": "bearer",
            }
        }


class UserResponseModel(BaseModel):
    """
    Schema for representing user response data.

    Attributes:
        username (str): The unique username of the user.
    """

    username: str = Field(
        ..., title="Username", description="The unique username of the user."
    )

    class Config:
        schema_extra = {"example": {"username": "john_doe"}}


class ContainerInfoModel(BaseModel):
    """
    Schema for representing Docker container information.

    Attributes:
        id (str): The unique identifier of the Docker container.
        name (str): The name of the Docker container.
        status (str): The current status of the Docker container.
        image (str): The Docker image used by the container.
    """

    id: str = Field(
        ...,
        title="Container ID",
        description="The unique identifier of the Docker container.",
    )
    name: str = Field(
        ..., title="Container Name", description="The name of the Docker container."
    )
    status: str = Field(
        ...,
        title="Container Status",
        description="The current status of the Docker container (e.g., running, exited).",
    )
    image: str = Field(
        ..., title="Image", description="The Docker image used by the container."
    )

    class Config:
        schema_extra = {
            "example": {
                "id": "e4c88bf1725a98abc...",
                "name": "web_app",
                "status": "running",
                "image": "nginx:latest",
            }
        }


class ContainerActionRequest(BaseModel):
    """
    Schema for requesting an action on a Docker container.

    Attributes:
        container_id (str): The unique identifier of the Docker container.
    """

    container_id: str = Field(
        ...,
        title="Container ID",
        description="The unique identifier of the Docker container.",
    )

    class Config:
        schema_extra = {"example": {"container_id": "e4c88bf1725a98abc..."}}


class CloneAndRunRequest(BaseModel):
    """
    Schema for cloning a GitHub repository and running a container.

    Attributes:
        github_url (str): The URL of the GitHub repository to clone.
        dockerfile_dir (str): The directory in the repository containing the Dockerfile.
    """

    github_url: str = Field(
        ...,
        title="GitHub URL",
        description="The URL of the GitHub repository to clone.",
    )
    dockerfile_dir: str = Field(
        "",
        title="Dockerfile Directory",
        description="The directory in the repository containing the Dockerfile.",
    )

    class Config:
        schema_extra = {
            "example": {
                "github_url": "https://github.com/example/repo.git",
                "dockerfile_dir": "/docker",
            }
        }


class ContainerStatsModel(BaseModel):
    """
    Schema for representing Docker container statistics.

    Attributes:
        cpu_usage (float): The percentage of CPU usage by the container.
        system_cpu_usage (float): The total CPU usage of the system.
        memory_usage (int): The memory usage of the container in bytes.
        memory_limit (int): The memory limit of the container in bytes.
        network_io (dict): The network input/output statistics of the container.
    """

    cpu_usage: float = Field(
        ...,
        title="CPU Usage",
        description="The percentage of CPU usage by the container.",
    )
    system_cpu_usage: float = Field(
        ..., title="System CPU Usage", description="The total CPU usage of the system."
    )
    memory_usage: int = Field(
        ...,
        title="Memory Usage",
        description="The memory usage of the container in bytes.",
    )
    memory_limit: int = Field(
        ...,
        title="Memory Limit",
        description="The memory limit of the container in bytes.",
    )
    network_io: dict = Field(
        ...,
        title="Network IO",
        description="The network input/output statistics of the container.",
    )

    class Config:
        schema_extra = {
            "example": {
                "cpu_usage": 2.5,
                "system_cpu_usage": 50.0,
                "memory_usage": 1048576,
                "memory_limit": 2097152,
                "network_io": {
                    "received": {"bytes": "1.0 MB", "packets": 120},
                    "transmitted": {"bytes": "0.5 MB", "packets": 80},
                },
            }
        }
