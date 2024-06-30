import asyncio
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from settings import settings

ID = "_id"
mongo_client = AsyncIOMotorClient(
    host=settings.MONGO_URL,
    minPoolSize=settings.MONGO_MIN_POOL,
    maxPoolSize=settings.MONGO_MAX_POOL,
)

### Collections
MATHCES = "matches"


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


async def init_db():
    databases = [
        mongo_client[settings.MONGO_TENNIS_MEN_DB],
        mongo_client[settings.MONGO_TENNIS_WOMEN_DB],
        mongo_client[settings.MONGO_FOOTBALL_DB],
        mongo_client[settings.MONGO_BASKETBALL_DB],
        mongo_client[settings.MONGO_HOCKEY_DB],
    ]

    match_indexes = [asyncio.create_task(create_match_indexes(db)) for db in databases]
    await asyncio.gather(*match_indexes)


if __name__ == "__main__":
    asyncio.run(init_db())
