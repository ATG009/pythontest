import os
from dotenv import dotenv_values


_env_values: dict = {
    **dotenv_values(".env"),
    **os.environ
}


class Config:
    MONGO_DATABASE: str = _env_values["MONGO_DATABASE"]
    MONGO_USER: str = _env_values["MONGO_USER"]
    MONGO_PASSWORD: str = _env_values["MONGO_PASSWORD"]
    MONGO_ADDRESS: str = _env_values["MONGO_ADDRESS"]
    MONGO_PORT: str = _env_values["MONGO_PORT"]
    MONGO_URI: str = "mongodb://{user}:{password}@{address}:{port}"

    BOT_API_TOKEN: str = _env_values["7030089430:AAE6YTggUR23euetg165aDhL73sERJc5iNc"]
    BOT_MAX_MESSAGE_SIZE: int = 4096
