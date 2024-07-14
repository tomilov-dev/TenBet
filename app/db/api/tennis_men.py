import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

sys.path.append(str(Path(__file__).parent.parent))
from settings import settings
from db.core import client
from api.base import BaseRepository
from data.tennis_men import TennisMenRepositoryInterface


class TennisMenRepository(
    BaseRepository,
    TennisMenRepositoryInterface,
):
    def __init__(self) -> None:
        BaseRepository.__init__(self, db=client[settings.MONGO_TENNIS_MEN_DB])
