import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from db.core import MATHCES
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
        return self.matches_collection.find_one(
            {"code": code},
            {"_id": 1, "code": 1, "status": 1, "error": 1},
        )

    async def find_codes(self, codes: list[str]) -> list[dict]:
        cursor = self.matches_collection.find(
            {"code": {"$in": codes}},
            {"_id": 1, "code": 1, "status": 1, "error": 1},
        )
        return [m async for m in cursor]

    async def add_match(self, match: MatchSDM) -> None:
        await self.matches_collection.insert_one(match.model_dump())

    async def add_matches(self, matches: list[MatchSDM]) -> None:
        await self.matches_collection.insert_many([m.model_dump() for m in matches])
