import sys
import json
import asyncio
import pytest
from pathlib import Path
from pydantic import BaseModel, ConfigDict

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(str(ROOT_DIR)))

from base_scraper import SportType, SPORT
from models import MatchOddsHA, MatchOdds1x2, OddsType
from betexplorer.scraper import BetExplorerScraper


DUMPS_PATH = ROOT_DIR / "betexplorer" / "tests" / "odds_dumps"


class OddsDumpTestCase(BaseModel):
    code: str
    sport: SportType

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_dump(self) -> MatchOddsHA | MatchOdds1x2:
        with open(DUMPS_PATH / f"{self.code}.json", "r") as file:
            data = json.loads(file.read())
            if self.sport.odds_type == OddsType.ODDS_HA:
                data = MatchOddsHA.model_validate(data)
            else:
                data = MatchOdds1x2.model_validate(data)
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
