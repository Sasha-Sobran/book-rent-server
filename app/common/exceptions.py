class InvalidJWTTokenException(Exception):
    pass


class UserNotFoundException(Exception):
    pass


class UserEmailNotUniqueException(Exception):
    pass


class UserDoesNotExistException(Exception):
    pass


class InvalidUserCredentialsException(Exception):
    pass


class InvalidRefreshTokenException(Exception):
    pass


class UserEmailDoesNotExistException(Exception):
    pass
