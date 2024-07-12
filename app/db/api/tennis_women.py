import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

sys.path.append(str(Path(__file__).parent.parent))
from api.base import BaseRepository, client, settings
from data.tennis_women import TennisWomenRepositoryInterface


class TennisWomenRepository(
    BaseRepository,
    TennisWomenRepositoryInterface,
):
    def __init__(self) -> None:
        BaseRepository.__init__(self, db=client[settings.MONGO_TENNIS_WOMEN_DB])
