from typing import Any
from pydantic import BaseModel, GetCoreSchemaHandler
from pydantic_core import core_schema, CoreSchema


class OddsType(str):
    """Odds type implemented in BetExplorer scraper"""

    ODDS_1x2 = "odds_1x2_type"
    ODDS_HA = "odds_ha_type"

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


class TournamentNameParsed(BaseModel):
    tournament_fullname: str

    qualification: bool = False
    tournament_category: str | None = None
    tournament_name: str | None = None
    tournament_stage: str | None = None


class MatchDescriptionSDM(TournamentNameParsed):
    """Description of FlashScore match"""

    code_t1: str
    code_t2: str
    full_name_t1: str
    full_name_t2: str
    short_name_t1: str
    short_name_t2: str

    winner: int | None
    reason: str

    start_date: int
    end_date: int

    score_t1: int | None = None
    score_t2: int | None = None

    infobox: str


class TimeScoreSDM(BaseModel):
    """Time Score of FlashScore match"""

    score_t1: int
    score_t2: int

    tiebreak_t1: int | None = None
    tiebreak_t2: int | None = None

    playtime: str | None = None


class PlayerSDM(BaseModel):
    """Data of FlashScore player"""

    id: str
    name: str
    country: str
    country_id: int
    rank: int
    link: str


class MatchCodeSDM(TournamentNameParsed):
    """Data of FlashScore match-code and match-date"""

    date: int
    code: str
    status: str

    def __hash__(self) -> str:
        return hash(str(self.code))

    def __eq__(self, other: "MatchCodeSDM") -> bool:
        if isinstance(other, MatchCodeSDM):
            if self.code == other.code:
                return True
        return False

    @classmethod
    def drop_dups(
        self,
        matches: list["MatchCodeSDM"],
    ) -> list["MatchCodeSDM"]:
        return list(set(matches))


class TournamentByYearUrlSDM(BaseModel):
    url: str
    start_year: int | None = None
    end_year: int | None = None


class TournamentSDM(BaseModel):
    """Data of FlashScore tournament"""

    category: str
    name: str
    archive_link: str
    by_year_urls: list[TournamentByYearUrlSDM] = []


class TournamentByYearSDM(BaseModel):
    """Data of FlashScore tournament in <year>"""

    league: str = ""
    season_id: str = ""
    page: int = 0

    events_count: int
    events_collected: int = 0

    codes: set[str] = set()

    def parsed(self) -> bool:
        if self.league == "" or self.season_id == "":
            return True
        if self.events_collected >= self.events_count:
            return True
        ### limit of requests count
        if self.page >= 9:
            return True
        return False

    def get_url(self) -> str:
        if self.parsed():
            return None

        self.page += 1
        url = "https://d.flashscore.co.uk/x/feed/"
        return url + f"tr_{self.league}_{self.season_id}_{self.page}_5_en-uk_1"

    def add_codes(self, codes: list[str]) -> None:
        codeset = set(codes)
        spreadset = codeset - self.codes
        self.events_collected += len(spreadset)
        self.codes.update(spreadset)


class TennisExplorerIDSDM(BaseModel):
    """Tennis Explorer ID for DataBase"""

    id: str


class RankSDM(BaseModel):
    """Tennis Ranking data from TennisExplorer"""

    te_id: str

    date: int
    rank: int
    points: int
    name: str


class TennisPlayerDataSDM(BaseModel):
    """Tennis Player data from TennixExplorer"""

    te_id: str

    name: str
    country: str | None = None
    height: int | None = None
    weight: int | None = None
    birthday: int | None = None
    plays: str | None = None
    career_start: int | None = None


class BookOddsHASDM(BaseModel):
    """Home/Away <bookmaker-name> odds data from BetExplorer"""

    name: str

    odds_t1: float
    odds_t2: float
    odds_date: int

    open_odds_t1: float | None
    open_odds_t2: float | None
    open_odds_date: int | None


class BookOdds1x2SDM(BookOddsHASDM):
    """1x2 <bookmaker-name> odds data from BetExplorer"""

    odds_x: float
    open_odds_x: float | None


class MatchOddsHASDM(BaseModel):
    """Match odds from BetExplorer: all bookmakers"""

    code: str

    is_odds: bool = True
    error: bool = False

    odds_type: OddsType = OddsType.ODDS_HA
    odds: list[BookOddsHASDM] = []


class MatchOdds1x2SDM(MatchOddsHASDM):
    odds_type: OddsType = OddsType.ODDS_1x2
    odds: list[BookOdds1x2SDM] = []


class MatchSDM(BaseModel):
    """Data of FlashScore match"""

    code: str
    error: bool = False
    status: str | None = None

    playtime: str | None = None

    time1: TimeScoreSDM | None = None
    time2: TimeScoreSDM | None = None
    time3: TimeScoreSDM | None = None
    time4: TimeScoreSDM | None = None
    time5: TimeScoreSDM | None = None

    description: MatchDescriptionSDM | None = None
    odds: MatchOddsHASDM | MatchOdds1x2SDM | None = None

    statistics1: dict = {}
    statistics2: dict = {}
