from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # TODO 1: database_url — required 
    database_url: str
    # TODO 2: sql_echo — boolean, False by default
    sql_echo: bool = False 


settings = Settings()