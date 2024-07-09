import sys
import asyncio
from pathlib import Path
from pymongo.errors import DuplicateKeyError

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from settings import settings
from service.base_scraper import SportType, SPORT
from service.tennisexplorer.scraper import (
    TennisExplorerRankScraper,
    TennisExplorerPlayerScraper,
    TennisExplorerRankDatesScraper,
)
from service.flashscore.scraper.tournament import (
    TournamentScraper,
    TournamentMatchesScraper,
)
from manager.base import BaseManager


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

    # res = await manager.add_matches([code1, code2, code3, code4])
    # print(res)

    # await manager.del_match(code)

    # data = await scraper.scrape(code)
    # print(data, "\n")
    # await coll.insert_one(data.model_dump())

    # record = await coll.find_one({"code": code})
    # print(record)


if __name__ == "__main__":
    asyncio.run(test())
