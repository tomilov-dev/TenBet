import asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError

from settings import settings
from mongo import mongo_client, MATHCES
from models import Match
from services.base_scraper import SportType, SPORT
from services.betexplorer.scraper import BetExplorerScraper
from services.flashscore.scraper.match import MatchScraper
from services.flashscore.scraper.player import PlayerScraper, PlayerMatchesScaper
from services.flashscore.scraper.week import WeeklyMatchesScraper
from services.tennisexplorer.scraper import (
    TennisExplorerRankScraper,
    TennisExplorerPlayerScraper,
    TennisExplorerRankDatesScraper,
)
from services.flashscore.scraper.tournament import (
    TournamentScraper,
    TournamentMatchesScraper,
)


class BaseManager:
    def __init__(
        self,
        sport: SportType,
        db: AsyncIOMotorDatabase,
    ):
        self.sport = sport

        self.db = db
        ### collections
        self.c_matches = db[MATHCES]

        self.match = MatchScraper(sport=sport)
        self.odds = BetExplorerScraper(sport=sport)
        self.tournament = TournamentScraper(sport=sport)
        self.tournament_matches = TournamentMatchesScraper(sport=sport)
        self.week = WeeklyMatchesScraper(sport=sport)

    async def find_code(self, code: str) -> Match | None:
        """Return match code and status if exists in the database"""

        data = await self.c_matches.find_one(
            {"code": code},
            {"_id": 1, "code": 1, "status": 1, "error": 1},
        )
        return None if data is None else Match(**data)

    async def find_codes(self, codes: list[str]) -> list[dict]:
        """Return match codes and statuses if codes exists in the database"""

        cursor = self.c_matches.find(
            {"code": {"$in": codes}},
            {"_id": 1, "code": 1, "status": 1, "error": 1},
        )
        return [Match(**m) async for m in cursor]

    async def add_match(self, code: str) -> Match | None:
        found = await self.find_code(code)
        if found:
            return None

        match_data = await self.match.scrape(code)
        odds_data = await self.odds.scrape(code)
        match_data.odds = odds_data

        await self.c_matches.insert_one(match_data.model_dump())
        return match_data

    async def add_matches(self, codes: list[str]) -> list[Match] | None:
        tasks = [asyncio.create_task(self.add_match(code)) for code in codes]
        matches = await asyncio.gather(*tasks)
        return [m for m in matches if m is not None]


class ManagerTennisMen(BaseManager):
    def __init__(
        self,
        sport: SportType,
        dbc: AsyncIOMotorCollection,
    ):
        super().__init__(sport, dbc)


async def test():
    manager = ManagerTennisMen(
        SPORT.TENNIS_MEN,
        mongo_client[settings.MONGO_TENNIS_MEN_DB],
    )

    code1 = "K831uSar"
    code2 = "p4jPCMAF"
    code3 = "21vkvxmJ"
    code4 = "fFsIWr4b"
    code5 = "lzQ1c8oJ"

    # res = await manager.add_match(code4)
    # res = await manager.find_code(code1)

    res = await manager.add_matches([code1, code2, code3, code4])
    print(res)

    # await manager.del_match(code)

    # data = await scraper.scrape(code)
    # print(data, "\n")
    # await coll.insert_one(data.model_dump())

    # record = await coll.find_one({"code": code})
    # print(record)


if __name__ == "__main__":
    asyncio.run(test())
