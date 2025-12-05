class Settings:
    encoding_algorithm: str = "HS256"
    access_token_expiration_time_in_minutes: int = 30
    refresh_token_expiration_time_in_days: int = 30
    encoding_key: str = "secret_key"
