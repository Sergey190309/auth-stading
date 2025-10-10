from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    pg_async_prefix: str = Field('postgresql+asyncpg', alias='PG_ASYNC_PREFIX')
    pg_user: str = Field('default_user', alias='PG_USER')
    pg_password: str = Field('default_password', alias='PG_PASSWORD')
    pg_host: str = Field('localhost', alias='PG_HOST')
    pg_port: str = Field('5432', alias='PG_PORT')
    pg_db: str = Field('default_db', alias='PG_DB')

    environment: Literal['dev', 'prod', 'test'] = 'dev'
    debug: bool = Field(False, alias='DEBUG')

    secret_key: str = Field('default_secret', alias='SECRET_KEY')
    algorithm: str = Field('HS256', alias='ALGORITHM')
    access_token_expire_minutes: int = Field(
        30, alias='ACCESS_TOKEN_EXPIRE_MINUTES')  

    model_config = SettingsConfigDict(
        env_file='.db.env',
        extra='ignore',
        populate_by_name=True
    )


settings: Settings = Settings() # type: ignore
# settings: Settings = Settings() # pyright: ignore[reportCallIssue]
