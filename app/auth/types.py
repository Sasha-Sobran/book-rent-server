import datetime
from enum import Enum, auto
from typing import NamedTuple


class JWTTokenType(Enum):
    access = auto()
    refresh = auto()


class JWTTokenPayload(NamedTuple):
    user_id: str
    token_type: str
    exp: datetime.datetime
    role_name: str
