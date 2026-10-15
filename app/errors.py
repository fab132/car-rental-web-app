"""Domain errors raised by the service layer.

The services do not know about HTTP. main.py maps these to status codes:
NotFoundError -> 404, ConflictError -> 409 (a business rule was broken).
Malformed input never reaches the services; Pydantic answers it with 422.
"""


class DomainError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    pass


class ConflictError(DomainError):
    pass
