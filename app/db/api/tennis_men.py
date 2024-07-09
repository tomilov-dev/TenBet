import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

sys.path.append(str(Path(__file__).parent.parent))
from api.base import BaseRepository
from data.tennis_men import TennisMenRepositoryInterface


class TennisMenRepository(
    BaseRepository,
    TennisMenRepositoryInterface,
):
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
