
from pydantic import BaseSettings

class Settings(BaseSettings):
    RIPPLED_SERVER_URL: str
    COINSTAT_API_URL : str
    ACCOUNT : str
    CURRENCY : str = 'EUR'
    API_USER_NAME : str
    API_USER_PASSWORD : str

    class Config:
        env_file = ".env"

settings = Settings()