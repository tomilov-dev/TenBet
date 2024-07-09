import sys
import asyncio
from pathlib import Path
import pytest
from pydantic import BaseModel, ConfigDict

sys.path.append(str(Path(__file__).parent.parent.parent))

from flashscore.common import SPORT, SportType
from flashscore.scraper.tournament import TournamentScraper, TournamentMatchesScraper


class TournamentTestCase(BaseModel):
    category_url: str
    tournament_url: str
    tournament_matches: int
    sport: SportType

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TournamentScraperBaseTest:
    @pytest.fixture
    def testcase(self) -> TournamentTestCase:
        return TournamentTestCase(
            category_url="",
            tournament_url="",
            tournament_matches=0,
            sport=SPORT.TENNIS_MEN,
        )

    @pytest.mark.asyncio
    async def test_tournaments_scraper(self, testcase: TournamentTestCase):
        scraper = TournamentScraper(sport=testcase.sport)
        tournaments = await scraper.scrape(testcase.category_url, limit=1)
        assert len(tournaments) == 1
        assert len(tournaments[0].by_year_urls) >= 1

    @pytest.mark.asyncio
    async def test_tournament_matches_scraper(self, testcase: TournamentTestCase):
        scraper = TournamentMatchesScraper(sport=testcase.sport)
        matches = await scraper.scrape(testcase.tournament_url)
        assert len(matches) == testcase.tournament_matches


class TestTournamentScraperTennisMen(TournamentScraperBaseTest):
    @pytest.fixture
    def testcase(self) -> TournamentTestCase:
        return TournamentTestCase(
            category_url="https://www.flashscore.co.uk/x/req/m_2_5724",
            tournament_url="https://www.flashscore.co.uk/tennis/atp-singles/australian-open-2023/results/",
            tournament_matches=239,
            sport=SPORT.TENNIS_MEN,
        )


class TestTournamentScraperTennisWomen(TournamentScraperBaseTest):
    @pytest.fixture
    def testcase(self) -> TournamentTestCase:
        return TournamentTestCase(
            category_url="https://www.flashscore.co.uk/x/req/m_2_5725",
            tournament_url="https://www.flashscore.co.uk/tennis/wta-singles/australian-open-2022/results/",
            tournament_matches=239,
            sport=SPORT.TENNIS_WOMEN,
        )


class TestTournamentScraperFootball(TournamentScraperBaseTest):
    @pytest.fixture
    def testcase(self) -> TournamentTestCase:
        return TournamentTestCase(
            category_url="https://www.flashscore.co.uk/x/req/m_1_198",
            tournament_url="https://www.flashscore.co.uk/football/england/premier-league-2022-2023/results/",
            tournament_matches=380,
            sport=SPORT.FOOTBALL,
        )


class TestTournamentScraperHockey(TournamentScraperBaseTest):
    @pytest.fixture
    def testcase(self) -> TournamentTestCase:
        return TournamentTestCase(
            category_url="https://www.flashscore.co.uk/x/req/m_4_200",
            tournament_url="https://www.flashscore.co.uk/ice-hockey/usa/nhl-2021-2022/results/",
            tournament_matches=1007,
            sport=SPORT.HOCKEY,
        )


class TestTournamentScraperBasketball(TournamentScraperBaseTest):
    @pytest.fixture
    def testcase(self) -> TournamentTestCase:
        return TournamentTestCase(
            category_url="https://www.flashscore.co.uk/x/req/m_3_200",
            tournament_url="https://www.flashscore.co.uk/basketball/usa/nba-2021-2022/results/",
            tournament_matches=1006,
            sport=SPORT.BASKETBALL,
        )
