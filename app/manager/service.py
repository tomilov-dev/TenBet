import re
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


class StatusCode:
    UNDEFINED = "undefined"

    mapper = {
        "1": "Future",
        "2": "Live",
        "3": "Finished",
        "4": "Postponed",
        "5": "Canceled",
        "6": "Extra Time",
        "7": "Penalties",
        "8": "Retired",
        "9": "Walkover",
        "10": "After Extra Time",
        "11": "After Penalties",
        "12": "1st Half",
        "13": "2nd Half",
        "14": "1st Period",
        "15": "2nd Period",
        "16": "3rd Period",
        "17": "Set 1",
        "18": "Set 2",
        "19": "Set 3",
        "20": "Set 4",
        "21": "Set 5",
        "22": "1st Quarter",
        "23": "2nd Quarter",
        "24": "3rd Quarter",
        "25": "4th Quarter",
        "26": "1st Inns",
        "27": "2nd Inns",
        "36": "Interrupted",
        "37": "Abandoned",
        "38": "Half Time",
        "42": "Awaiting updates",
        "43": "Delayed",
        "45": "To finish",
        "46": "Break Time",
        "47": "Set 1 - Tiebreak",
        "48": "Set 2 - Tiebreak",
        "49": "Set 3 - Tiebreak",
        "50": "Set 4 - Tiebreak",
        "51": "Set 5 - Tiebreak",
        "54": "Awarded",
        "55": "Set 6",
        "56": "Set 7",
        "57": "After day 1",
        "58": "After day 2",
        "59": "After day 3",
        "60": "After day 4",
        "61": "After day 5",
        "324": "Set 8",
        "325": "Set 9",
        "326": "Set 10",
        "327": "Set 11",
        "328": "Set 12",
        "329": "Set 13",
        "333": "Lunch",
        "334": "Tea",
        "335": "Medical timeout",
        UNDEFINED: "Error",
    }

    future_set = set(
        [
            mapper["1"],
            mapper["43"],
        ]
    )

    live_set = set(
        [
            mapper["2"],
            mapper["6"],
            mapper["7"],
            mapper["12"],
            mapper["13"],
            mapper["14"],
            mapper["15"],
            mapper["16"],
            mapper["17"],
            mapper["18"],
            mapper["19"],
            mapper["20"],
            mapper["21"],
            mapper["22"],
            mapper["23"],
            mapper["24"],
            mapper["25"],
            mapper["26"],
            mapper["27"],
            mapper["36"],
            mapper["38"],
            mapper["45"],
            mapper["46"],
            mapper["47"],
            mapper["48"],
            mapper["49"],
            mapper["50"],
            mapper["51"],
            mapper["55"],
            mapper["56"],
            mapper["57"],
            mapper["58"],
            mapper["59"],
            mapper["60"],
            mapper["61"],
            mapper["324"],
            mapper["325"],
            mapper["326"],
            mapper["327"],
            mapper["328"],
            mapper["329"],
            mapper["333"],
            mapper["334"],
            mapper["335"],
        ]
    )

    finished_set = set(
        [
            mapper["3"],
            mapper["4"],  # it's postponed but next match will have another code
            mapper["5"],
            mapper["8"],
            mapper["9"],
            mapper["10"],
            mapper["11"],
            mapper["37"],
            mapper["54"],
        ]
    )

    @classmethod
    def extract(cls, rx: re.Pattern, text: str) -> str:
        status_code = rx.search(text)
        if status_code:
            status_code = status_code.group(1)
        else:
            status_code = cls.UNDEFINED

        return cls.get(status_code)

    @classmethod
    def get(cls, code: str) -> str:
        if code in cls.mapper:
            return cls.mapper.get(code)
        return cls.mapper.get(cls.UNDEFINED)

    @classmethod
    def undefined(cls) -> str:
        return cls.mapper.get(cls.UNDEFINED)

    @classmethod
    def future(self, status: str) -> bool:
        if status in self.future_set:
            return True
        return False

    @classmethod
    def live(self, status: str) -> bool:
        if status in self.live_set:
            return True
        return False

    @classmethod
    def finished(self, status: str) -> bool:
        if status in self.finished_set:
            return True
        return False
