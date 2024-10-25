# domain/exceptions.py

class DomainException(Exception):
    """Base exception for domain errors."""
    pass

class AuthenticationException(DomainException):
    """Raised when authentication fails."""
    pass

class UserAlreadyExistsException(DomainException):
    """Raised when a user already exists."""
    pass

class InvalidTokenException(DomainException):
    """Raised when a token is invalid."""
    pass

class ContainerNotFoundException(DomainException):
    """Raised when a container is not found."""
    pass

class DockerAPIException(DomainException):
    """Raised for Docker API errors."""
    pass
