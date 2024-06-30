from typing import Any, Optional
from pydantic import BaseModel, GetCoreSchemaHandler, Field
from pydantic.functional_validators import AfterValidator
from pydantic_core import core_schema, CoreSchema
from bson import ObjectId


class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: Any,
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.chain_schema(
                        [
                            core_schema.str_schema(),
                            core_schema.no_info_plain_validator_function(cls.validate),
                        ]
                    ),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def validate(cls, value) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")

        return ObjectId(value)


class OddsType(str):
    """Odds type implemented in BetExplorer scraper"""

    ODDS_1x2 = "odds_1x2_type"
    ODDS_HA = "odds_ha_type"

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


class MatchDescription(BaseModel):
    """Description of FlashScore match"""

    tournament: str

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


class TimeScore(BaseModel):
    """Time Score of FlashScore match"""

    score_t1: int
    score_t2: int

    tiebreak_t1: int | None = None
    tiebreak_t2: int | None = None

    playtime: str | None = None


class Player(BaseModel):
    """Data of FlashScore player"""

    id: str
    name: str
    country: str
    country_id: int
    rank: int
    link: str


class MatchCode(BaseModel):
    """Data of FlashScore match-code"""

    date: int
    code: str

    def __hash__(self) -> str:
        return hash(str(self.code))

    def __eq__(self, other: "MatchCode") -> bool:
        if isinstance(other, MatchCode):
            if self.code == other.code:
                return True
        return False

    @classmethod
    def drop_dups(
        self,
        matches: list["MatchCode"],
    ) -> list["MatchCode"]:
        return list(set(matches))


class Tournament(BaseModel):
    """Data of FlashScore tournament"""

    category: str
    name: str
    archive_link: str
    by_year_urls: list[str] = []


class TournamentByYear(BaseModel):
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


class WeekMatch(MatchCode):
    """Data of FlashScore recent or future match: code, date & status"""

    status: str


class WeekTournament(BaseModel):
    """Data of FlashScore recent or future tournament"""

    name: str
    matches: list[WeekMatch]


class TennisExplorerID(BaseModel):
    """Tennis Explorer ID for DataBase"""

    id: str


class Rank(BaseModel):
    """Tennis Ranking data from TennisExplorer"""

    te_id: str

    date: int
    rank: int
    points: int
    name: str


class TennisPlayerData(BaseModel):
    """Tennis Player data from TennixExplorer"""

    te_id: str

    name: str
    country: str | None = None
    height: int | None = None
    weight: int | None = None
    birthday: int | None = None
    plays: str | None = None
    career_start: int | None = None


class BookOddsHA(BaseModel):
    """Home/Away <bookmaker-name> odds data from BetExplorer"""

    name: str

    odds_t1: float
    odds_t2: float
    odds_date: int

    open_odds_t1: float | None
    open_odds_t2: float | None
    open_odds_date: int | None


class BookOdds1x2(BookOddsHA):
    """1x2 <bookmaker-name> odds data from BetExplorer"""

    odds_x: float
    open_odds_x: float | None


class MatchOddsHA(BaseModel):
    """Match odds from BetExplorer: all bookmakers"""

    code: str

    is_odds: bool = True
    error: bool = False

    odds_type: OddsType = OddsType.ODDS_HA
    odds: list[BookOddsHA] = []


class MatchOdds1x2(MatchOddsHA):
    odds_type: OddsType = OddsType.ODDS_1x2
    odds: list[BookOdds1x2] = []


class Match(BaseModel):
    """Data of FlashScore match"""

    # id: Optional[PyObjectId] = Field(default=None, alias="_id")

    code: str
    error: bool = False
    status: str | None = None

    playtime: str | None = None

    time1: TimeScore | None = None
    time2: TimeScore | None = None
    time3: TimeScore | None = None
    time4: TimeScore | None = None
    time5: TimeScore | None = None

    description: MatchDescription | None = None
    odds: MatchOddsHA | MatchOdds1x2 | None = None

    statistics1: dict = {}
    statistics2: dict = {}
