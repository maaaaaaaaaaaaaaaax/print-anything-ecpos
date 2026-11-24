from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_token: str = Field(min_length=1)
    allowed_user_ids: Annotated[frozenset[int], NoDecode]

    @field_validator("telegram_token")
    @classmethod
    def validate_telegram_token(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("TELEGRAM_TOKEN must not be blank")
        return value

    @field_validator("allowed_user_ids", mode="before")
    @classmethod
    def parse_allowed_user_ids(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        parts = [part.strip() for part in value.split(",")]
        if not parts or any(not part.isascii() or not part.isdigit() for part in parts):
            raise ValueError("ALLOWED_USER_IDS must be comma-separated positive user IDs")
        user_ids = frozenset(int(part) for part in parts)
        if any(user_id <= 0 for user_id in user_ids):
            raise ValueError("ALLOWED_USER_IDS must contain positive user IDs")
        return user_ids
