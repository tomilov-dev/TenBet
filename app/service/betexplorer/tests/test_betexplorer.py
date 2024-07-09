import sys
import json
import asyncio
import pytest
from pathlib import Path
from pydantic import BaseModel, ConfigDict

ROOT_DIR = Path(__file__).parent.parent.parent
PROJ_DIR = ROOT_DIR.parent
sys.path.append(str(str(PROJ_DIR)))

from model.service import MatchOddsHASDM, MatchOdds1x2SDM, OddsType
from manager.service import SportType, SPORT
from service.betexplorer.scraper import BetExplorerScraper


DUMPS_PATH = ROOT_DIR / "betexplorer" / "tests" / "odds_dumps"


class OddsDumpTestCase(BaseModel):
    code: str
    sport: SportType

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_dump(self) -> MatchOddsHASDM | MatchOdds1x2SDM:
        with open(DUMPS_PATH / f"{self.code}.json", "r") as file:
            data = json.loads(file.read())
            if self.sport.odds_type == OddsType.ODDS_HA:
                data = MatchOddsHASDM.model_validate(data)
            else:
                data = MatchOdds1x2SDM.model_validate(data)
            return data

    async def dump_it(self) -> None:
        match = await BetExplorerScraper(sport=self.sport).scrape(self.code)
        with open(DUMPS_PATH / f"{match.code}.json", "w") as file:
            data = json.dumps(match.model_dump())
            file.write(data)


DUMP_TESTCASES = [
    OddsDumpTestCase(code="K831uSar", sport=SPORT.TENNIS_MEN),
    OddsDumpTestCase(code="hMwfbhsh", sport=SPORT.FOOTBALL),
]


class OddsScraperDumpTest:
    @pytest.fixture
    def testcase(self) -> OddsDumpTestCase:
        return OddsDumpTestCase(code="K831uSar", sport=SPORT.TENNIS_MEN)

    @pytest.mark.asyncio
    async def test_match_scraper(self, testcase: OddsDumpTestCase):
        scraper = BetExplorerScraper(sport=testcase.sport)
        odds = await scraper.scrape(testcase.code)
        dump = testcase.get_dump()

        assert odds == dump


class TestOddsScraperDumpTennisMen(OddsScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> OddsDumpTestCase:
        return DUMP_TESTCASES[0]


class TestOddsScraperDumpFootball(OddsScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> OddsDumpTestCase:
        return DUMP_TESTCASES[1]


async def upload_testcases():
    tasks = [t.dump_it() for t in DUMP_TESTCASES]
    await asyncio.gather(*tasks)


# if __name__ == "__main__":
#     asyncio.run(upload_testcases())
