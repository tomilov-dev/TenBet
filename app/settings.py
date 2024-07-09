from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent


class Settings(BaseSettings):
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_MIN_POOL: int
    MONGO_MAX_POOL: int

    MONGO_TENNIS_MEN_DB: str
    MONGO_TENNIS_WOMEN_DB: str
    MONGO_FOOTBALL_DB: str
    MONGO_BASKETBALL_DB: str
    MONGO_HOCKEY_DB: str

    SCRAPER_MAX_TRIES: int

    FLASHSCORE_MAX_RATE: int = 40
    FLASHSCORE_RATE_PERIOD: int = 1

    BETEXPLORER_MAX_RATE: int = 20
    BETEXPLORER_RATE_PERIOD: int = 1

    TENNISEXPLORER_MAX_RATE: int = 20
    TENNISEXPLORER_RATE_PERIOD: int = 1

    @property
    def MONGO_URL(self) -> str:
        return f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}"


settings = Settings(_env_file=ROOT_DIR / ".env")
