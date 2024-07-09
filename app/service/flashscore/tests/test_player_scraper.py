import sys
import asyncio
from pathlib import Path
import pytest
from pydantic import BaseModel, ConfigDict

sys.path.append(str(Path(__file__).parent.parent.parent))

from flashscore.common import SPORT, SportType
from flashscore.scraper.player import PlayerScraper, PlayerMatchesScaper


class PlayerTestCase(BaseModel):
    rank_url: str
    sport: SportType
    player_count: int

    model_config = ConfigDict(arbitrary_types_allowed=True)


class PlayerScraperBaseTest:
    @pytest.fixture
    def testcase(self) -> PlayerTestCase:
        return PlayerTestCase(rank_url="", sport=SPORT.TENNIS_MEN, player_count=100)

    @pytest.mark.asyncio
    async def test_player_scraper(self, testcase: PlayerTestCase):
        scraper = PlayerScraper(sport=testcase.sport)
        players = await scraper.scrape(testcase.rank_url)
        assert len(players) >= testcase.player_count

    @pytest.mark.asyncio
    async def test_player_matches_scraper(self, testcase: PlayerTestCase):
        player_scraper = PlayerScraper(sport=testcase.sport)
        matches_scraper = PlayerMatchesScaper(sport=testcase.sport)
        players = await player_scraper.scrape(testcase.rank_url)
        assert len(players) >= testcase.player_count
        matches = await matches_scraper.scrape(players[0], 1)
        assert len(matches) >= 10


class TestPlayerScraperTennisMen(PlayerScraperBaseTest):
    @pytest.fixture
    def testcase(self) -> PlayerTestCase:
        return PlayerTestCase(
            rank_url="https://d.flashscore.co.uk/x/feed/ran_dSJr14Y8_1",
            sport=SPORT.TENNIS_MEN,
            player_count=100,
        )


class TestPlayerScraperTennisWomen(PlayerScraperBaseTest):
    @pytest.fixture
    def testcase(self) -> PlayerTestCase:
        return PlayerTestCase(
            rank_url="https://d.flashscore.co.uk/x/feed/ran_hfDiar3L_1",
            sport=SPORT.TENNIS_MEN,
            player_count=100,
        )
