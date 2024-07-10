import sys
from pathlib import Path
from abc import ABC, abstractmethod
from pydantic import BaseModel

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))
from model.service import (
    OddsType,
    MatchOddsHASDM,
    MatchOdds1x2SDM,
    MatchSDM,
    PlayerSDM,
    MatchCodeSDM,
    TournamentSDM,
    RankSDM,
    TennisPlayerDataSDM,
)


class SportType(BaseModel):
    name: str
    tag: str
    prefix: str
    week_prefix: str
    stat_prefix: str
    stat_splitter: str
    odds_type: OddsType

    tennis_explorer: str | None = None

    _ranking_links: list[str] = []

    @property
    def ranking(self):
        if self._ranking_links:
            return self._ranking_links
        return []


class SPORT:
    FOOTBALL = SportType(
        name="football",
        tag="football",
        prefix="pr_1",
        week_prefix="f_1",
        stat_prefix="st",
        stat_splitter="¬SG÷",
        odds_type=OddsType.ODDS_1x2,
    )

    TENNIS_MEN = SportType(
        name="tennis",
        tag="tennis",
        prefix="pr_2",
        week_prefix="f_2",
        stat_prefix="st",
        stat_splitter="¬~SG÷",
        odds_type=OddsType.ODDS_HA,
        tennis_explorer="https://www.tennisexplorer.com/ranking/atp-men/",
    )

    TENNIS_WOMEN = SportType(
        name="tennis",
        tag="tennis",
        prefix="pr_2",
        week_prefix="f_2",
        stat_prefix="st",
        stat_splitter="¬~SG÷",
        odds_type=OddsType.ODDS_HA,
        tennis_explorer="https://www.tennisexplorer.com/ranking/wta-women/",
    )

    BASKETBALL = SportType(
        name="basketball",
        tag="basketball",
        prefix="pr_3",
        week_prefix="f_3",
        stat_prefix="st",
        stat_splitter="¬~SG÷",
        odds_type=OddsType.ODDS_1x2,
    )

    HOCKEY = SportType(
        name="hockey",
        tag="hockey",
        prefix="pr_4",
        week_prefix="f_4",
        stat_prefix="st",
        stat_splitter="¬~SG÷",
        odds_type=OddsType.ODDS_1x2,
    )


class ScraperInterface(ABC):
    def __init__(self, sport: SportType) -> None:
        self.sport = sport


class BetExplorerScraperInterface(ScraperInterface, ABC):
    @abstractmethod
    async def scrape_ha(self, code: str) -> MatchOddsHASDM:
        pass

    @abstractmethod
    async def scrape_1x2(self, code: str) -> MatchOdds1x2SDM:
        pass

    @abstractmethod
    async def scrape(self, code: str) -> MatchOddsHASDM | MatchOdds1x2SDM:
        pass


class FlashScoreMatchScraperInterface(ScraperInterface, ABC):
    @abstractmethod
    async def scrape(self, code: str) -> MatchSDM:
        pass


class FlashScorePlayerScraperInterface(ScraperInterface, ABC):
    @abstractmethod
    async def scrape(self, rank_url: str) -> list[PlayerSDM]:
        pass


class FlashScorePlayerMatchesScraperInterface(ScraperInterface, ABC):
    @abstractmethod
    async def scrape(self, player: PlayerSDM, page_limit: int) -> list[MatchCodeSDM]:
        pass


class FlashScoreTournamentScraperInterface(ScraperInterface, ABC):
    @abstractmethod
    async def scrape(
        self, category_url: str, limit: int | None = None
    ) -> list[TournamentSDM]:
        pass


class FlashScoreTournamentMatchesScraperIntefrace(ScraperInterface, ABC):
    @abstractmethod
    async def scrape(self, url: str) -> list[MatchCodeSDM]:
        pass


class FlashScoreWeeklyMatchesScraper(ScraperInterface, ABC):
    @abstractmethod
    async def scrape(self, days: list[int]) -> list[MatchCodeSDM]:
        pass


class TennisExplorerRankDatesScraperInterface(ScraperInterface, ABC):
    @abstractmethod
    async def scrape(self, min_y: int, max_y: int) -> list[str]:
        pass


class TennisExplorerRankScraperInterface(ScraperInterface, ABC):
    @abstractmethod
    async def scrape(self, dates: list[str]) -> list[RankSDM]:
        pass


class TennisExplorerPlayerScraperInterface(ScraperInterface, ABC):
    @abstractmethod
    async def scrape(self, tennis_explorer_id: str) -> TennisPlayerDataSDM:
        pass


### Day Codes (Flash Score Weekly Scraper)
LAST_WEEK_DAYS = [
    -7,
    -6,
    -5,
    -4,
    -3,
    -2,
    -1,
    0,
]  # 0 because today can be some finished matches
FUTURE_DAYS = [0, 1]
YESTERDAY_DAYS = [-1]
