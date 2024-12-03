class DomainException(Exception):
    pass


class AuthenticationException(DomainException):
    pass


class UserAlreadyExistsException(DomainException):
    pass


class InvalidTokenException(DomainException):
    pass


class ContainerNotFoundException(DomainException):
    pass


class DockerAPIException(DomainException):
    pass
