import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from settings import settings
from db.core import MATHCES, client, CURRENT
from data.base import RepositoryInterface
from model.service import MatchSDM


class BaseRepository(RepositoryInterface):
    def __init__(
        self,
        db: AsyncIOMotorDatabase,
    ) -> None:
        self.db = db

        self.matches_collection = self.db[MATHCES]
        self.current_collection = self.db[CURRENT]

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
        try:
            await self.matches_collection.insert_many(matches, ordered=False)
        except BulkWriteError as ex:
            for error in ex.details.get("writeErrors", []):
                doc = error.get("op")
                code = doc.get("code", None)
                if error.get("code") == 11000:  # Код ошибки дублирования
                    print(f"Duplicate error for document: {code}")
                else:
                    print(f"Other write error: {code}")

    async def get_match(self, code: str) -> dict | None:
        return await self.matches_collection.find_one({"code": code})

    async def get_matches(self, codes: str) -> list[dict] | None:
        cursor = self.matches_collection.find({"code": {"$in": codes}})
        return [m async for m in cursor]

    async def upsert_current_match(self, match: dict) -> None:
        await self.current_collection.update_one(
            filter={"code": match["code"]},
            update={"$set": match},
            upsert=True,
        )

    async def upsert_current_matches(self, matches: list[dict]) -> None:
        operations = [
            UpdateOne(
                filter={"code": match["code"]},
                update={"$set": match},
                upsert=True,
            )
            for match in matches
        ]

        if not operations:
            return None

        await self.current_collection.bulk_write(operations)

    async def get_current_match(self, code: str) -> dict | None:
        return await self.current_collection.find_one({"code": code})

    async def get_current_matches(self, codes: list[str]) -> list[dict] | None:
        cursor = self.current_collection.find({"code": {"$in": codes}})
        return [m async for m in cursor]

    async def get_all_current_matches(self) -> list[dict] | None:
        cursor = self.current_collection.find()
        return [m async for m in cursor]

    async def get_current_codes(self) -> list[dict] | None:
        cursor = self.current_collection.find(
            {},
            {"_id": 1, "code": 1, "status": 1, "error": 1},
        )
        return [m async for m in cursor]

    async def delete_current_match(self, code: str) -> None:
        await self.current_collection.delete_one(filter={"code": code})

    async def delete_current_matches(self, codes: list[str]) -> None:
        await self.current_collection.delete_many(filter={"code": {"$in": codes}})
