from pydantic import BaseModel


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RegisterRequest(BaseModel):
    password: str
    name: str
    email: str


class RegisterResponse(BaseModel):
    user_id: int
    name: str
    phone_number: str
    role_id: int


class TokenRefreshInputSchema(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class TokenObtainByRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class UserSelfResponse(BaseModel):
    user_id: int
    name: str
    surname: str
    email: str
    phone_number: None | str
    role_name: str
