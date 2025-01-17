import sys
from pathlib import Path
import asyncio
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

sys.path.append(str(Path(__file__).parent.parent))
from settings import settings

ID = "_id"
client = AsyncIOMotorClient(
    host=settings.MONGO_URL,
    minPoolSize=settings.MONGO_MIN_POOL,
    maxPoolSize=settings.MONGO_MAX_POOL,
)

### Collections
MATHCES = "matches"
CURRENT = "current_matches"
PREDICTIONS = "predictions"


async def create_match_indexes(db: AsyncIOMotorDatabase):
    await db[MATHCES].create_indexes(
        [
            pymongo.IndexModel(
                [("code", pymongo.ASCENDING)],
                unique=True,
            ),
            pymongo.IndexModel(
                [("status", pymongo.ASCENDING)],
                unique=False,
            ),
            pymongo.IndexModel(
                [("description.code_t1", pymongo.ASCENDING)],
                unique=False,
            ),
            pymongo.IndexModel(
                [("description.code_t2", pymongo.ASCENDING)],
                unique=False,
            ),
            pymongo.IndexModel(
                [("description.start_date", pymongo.ASCENDING)],
                unique=False,
            ),
            pymongo.IndexModel(
                [("description.end_date", pymongo.ASCENDING)],
                unique=False,
            ),
        ]
    )


async def create_current_indexes(db: AsyncIOMotorDatabase):
    await db[CURRENT].create_indexes(
        [
            pymongo.IndexModel(
                [("code", pymongo.ASCENDING)],
                unique=True,
            ),
        ]
    )


async def create_predictions_indexes(db: AsyncIOMotorDatabase):
    await db[PREDICTIONS].create_indexes(
        [
            pymongo.IndexModel(
                [("code", pymongo.ASCENDING)],
                unique=True,
            ),
        ]
    )


async def init_db():
    databases = [
        client[settings.MONGO_TENNIS_MEN_DB],
        client[settings.MONGO_TENNIS_WOMEN_DB],
        client[settings.MONGO_FOOTBALL_DB],
        client[settings.MONGO_BASKETBALL_DB],
        client[settings.MONGO_HOCKEY_DB],
    ]

    match_indexes = [asyncio.create_task(create_match_indexes(db)) for db in databases]
    await asyncio.gather(*match_indexes)

    ### current means matches that are not finished yet (future or alive)
    current_indexes = [
        asyncio.create_task(create_current_indexes(db)) for db in databases
    ]
    await asyncio.gather(*current_indexes)

    predictions_indexes = [
        asyncio.create_task(create_predictions_indexes(db)) for db in databases
    ]
    await asyncio.gather(*predictions_indexes)


if __name__ == "__main__":
    asyncio.run(init_db())
