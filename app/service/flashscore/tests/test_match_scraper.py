import sys
import asyncio
from pathlib import Path
import pytest
from pydantic import BaseModel, ConfigDict
import json

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(str(ROOT_DIR)))


from flashscore.common import SPORT, SportType
from flashscore.scraper.match import MatchScraper, MatchSDM


class MatchDumpTestCase(BaseModel):
    code: str
    sport: SportType

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def get_dump(self) -> MatchSDM:
        with open(
            ROOT_DIR / "flashscore" / "tests" / "match_dumps" / f"{self.code}.json"
        ) as file:
            data = json.loads(file.read())
            data = MatchSDM.model_validate(data)
            return data

    async def dump_it(self) -> None:
        match = await MatchScraper(sport=self.sport).scrape(self.code)

        with open(
            ROOT_DIR / "flashscore" / "tests" / "match_dumps" / f"{match.code}.json",
            "w",
        ) as file:
            data = json.dumps(match.model_dump())
            file.write(data)


DUMP_TESTCASES = [
    MatchDumpTestCase(code="K831uSar", sport=SPORT.TENNIS_MEN),
    MatchDumpTestCase(code="GbTw0PTG", sport=SPORT.TENNIS_MEN),
    MatchDumpTestCase(code="UDqhp2CG", sport=SPORT.TENNIS_MEN),
    MatchDumpTestCase(code="txVeOAp4", sport=SPORT.TENNIS_MEN),
    MatchDumpTestCase(code="QTbabtYh", sport=SPORT.TENNIS_MEN),
    MatchDumpTestCase(code="IBHXWNNC", sport=SPORT.TENNIS_MEN),
    MatchDumpTestCase(code="baKwLt6C", sport=SPORT.TENNIS_MEN),
    MatchDumpTestCase(code="UVpnRkml", sport=SPORT.TENNIS_WOMEN),
    MatchDumpTestCase(code="M1w8YmqE", sport=SPORT.FOOTBALL),
    MatchDumpTestCase(code="ro9gcXlC", sport=SPORT.HOCKEY),
    MatchDumpTestCase(code="CdcbfwIf", sport=SPORT.BASKETBALL),
]


class MatchScraperDumpTest:
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return MatchDumpTestCase(code="K831uSar", sport=SPORT.TENNIS_MEN)

    @pytest.mark.asyncio
    async def test_match_scraper(self, testcase: MatchDumpTestCase):
        scraper = MatchScraper(sport=testcase.sport)
        match = await scraper.scrape(testcase.code)
        dump = testcase.get_dump()

        assert match == dump


class TestMatchScraperDumpTennisMen(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[0]


class TestMatchScraperDumpTennisMenTiebreaks(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[1]


class TestMatchScraperDumpTennisMenWalkover(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[2]


class TestMatchScraperDumpTennisMenRetired(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[3]


class TestMatchScraperDumpTennisMenInfobox(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[4]


class TestMatchScraperDumpTennisMenAwarded(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[5]


class TestMatchScraperDumpTennisMenCancelled(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[6]


class TestMatchScraperDumpTennisWomen(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[7]


class TestMatchScraperDumpFootball(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[8]


class TestMatchScraperDumpHockey(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[9]


class TestMatchScraperDumpBasketball(MatchScraperDumpTest):
    @pytest.fixture
    def testcase(self) -> MatchDumpTestCase:
        return DUMP_TESTCASES[10]


async def upload_testcases():
    tasks = [t.dump_it() for t in DUMP_TESTCASES]
    await asyncio.gather(*tasks)


# if __name__ == "__main__":
#     asyncio.run(upload_testcases())
