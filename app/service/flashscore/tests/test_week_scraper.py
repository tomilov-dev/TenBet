import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).parent.parent.parent))

from flashscore.common import SPORT, StatusCode
from flashscore.scraper.week import WeeklyMatchesScraper, FUTURE_DAYS
from flashscore.scraper.match import MatchScraper


class WeekScraperBaseTest:
    @pytest.fixture
    def week_scraper(self) -> WeeklyMatchesScraper:
        return WeeklyMatchesScraper(sport=SPORT.TENNIS_MEN)

    @pytest.fixture
    def match_scraper(self) -> MatchScraper:
        return MatchScraper(sport=SPORT.TENNIS_MEN)

    @pytest.mark.asyncio
    async def test_week_scraper(self, week_scraper: WeeklyMatchesScraper):
        tournaments = await week_scraper.scrape(FUTURE_DAYS)
        assert len(tournaments) > 0
        assert len(tournaments[0].matches) > 0

    @pytest.mark.asyncio
    async def test_future_matches_scraper(
        self,
        week_scraper: WeeklyMatchesScraper,
        match_scraper: MatchScraper,
    ):
        tournaments = await week_scraper.scrape(FUTURE_DAYS)
        assert len(tournaments) > 0

        target_match = None
        for tournament in tournaments:
            if target_match is not None:
                break

            if tournament.matches:
                for match in tournament.matches:
                    if match.status == StatusCode.get("1"):
                        target_match = match
                        break

        if target_match is not None:
            match = await match_scraper.scrape(target_match.code)

            assert match.code == target_match.code
            assert match.status == StatusCode.get("1")
            assert match.playtime == None


class TestWeekScraperTennisMen(WeekScraperBaseTest):
    @pytest.fixture
    def week_scraper(self) -> WeeklyMatchesScraper:
        return WeeklyMatchesScraper(sport=SPORT.TENNIS_MEN)

    @pytest.fixture
    def match_scraper(self) -> MatchScraper:
        return MatchScraper(sport=SPORT.TENNIS_MEN)


class TestWeekScraperTennisWomen(WeekScraperBaseTest):
    @pytest.fixture
    def week_scraper(self) -> WeeklyMatchesScraper:
        return WeeklyMatchesScraper(sport=SPORT.TENNIS_WOMEN)

    @pytest.fixture
    def match_scraper(self) -> MatchScraper:
        return MatchScraper(sport=SPORT.TENNIS_WOMEN)


class TestWeekScraperFootball(WeekScraperBaseTest):
    @pytest.fixture
    def week_scraper(self) -> WeeklyMatchesScraper:
        return WeeklyMatchesScraper(sport=SPORT.FOOTBALL)

    @pytest.fixture
    def match_scraper(self) -> MatchScraper:
        return MatchScraper(sport=SPORT.FOOTBALL)


class TestWeekScraperHockey(WeekScraperBaseTest):
    @pytest.fixture
    def week_scraper(self) -> WeeklyMatchesScraper:
        return WeeklyMatchesScraper(sport=SPORT.HOCKEY)

    @pytest.fixture
    def match_scraper(self) -> MatchScraper:
        return MatchScraper(sport=SPORT.HOCKEY)


class TestWeekScraperBasketball(WeekScraperBaseTest):
    @pytest.fixture
    def week_scraper(self) -> WeeklyMatchesScraper:
        return WeeklyMatchesScraper(sport=SPORT.BASKETBALL)

    @pytest.fixture
    def match_scraper(self) -> MatchScraper:
        return MatchScraper(sport=SPORT.BASKETBALL)
