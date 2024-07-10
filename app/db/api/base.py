import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from settings import settings
from db.core import MATHCES, client
from data.base import RepositoryInterface
from model.service import MatchSDM


class BaseRepository(RepositoryInterface):
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
    ) -> None:
        self.db = db

        self.matches_collection = self.db[MATHCES]

    async def find_code(self, code: str) -> dict:
        return await self.matches_collection.find_one(
            {"code": code},
            {"_id": 1, "code": 1, "status": 1, "error": 1},
        )

    async def find_codes(self, codes: list[str]) -> list[dict]:
        cursor = self.matches_collection.find(
            {"code": {"$in": codes}},
            {"_id": 1, "code": 1, "status": 1, "error": 1},
        )
        return [m async for m in cursor]

    async def add_match(self, match: dict) -> None:
        await self.matches_collection.insert_one(match)

    async def add_matches(self, matches: list[dict]) -> None:
        await self.matches_collection.insert_many(matches)
