import sys
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from pymongo.errors import DuplicateKeyError

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from model.service import MatchSDM
from manager.base import (
    BaseManager,
    BaseDataInterface,
    TournamentsManagerMixin,
    PlayersManagerMixin,
    BasePredictorInterface,
)
from manager.service import (
    SportType,
    FlashScoreMatchScraperInterface,
    BetExplorerScraperInterface,
    FlashScoreTournamentScraperInterface,
    FlashScoreTournamentMatchesScraperIntefrace,
    FlashScoreWeeklyMatchesScraper,
    FlashScorePlayerScraperInterface,
    FlashScorePlayerMatchesScraperInterface,
)


class TennisWomenDataInterface(BaseDataInterface):
    pass


class TennisWomenManager(
    BaseManager,
    TournamentsManagerMixin,
    PlayersManagerMixin,
):
    def __init__(
        self,
        sport: SportType,
        data: BaseDataInterface,
        match: FlashScoreMatchScraperInterface,
        week: FlashScoreWeeklyMatchesScraper,
        odds: BetExplorerScraperInterface,
        tournament: FlashScoreTournamentScraperInterface,
        tournament_matches: FlashScoreTournamentMatchesScraperIntefrace,
        player: FlashScorePlayerScraperInterface,
        player_matches: FlashScorePlayerMatchesScraperInterface,
        predictor: BasePredictorInterface,
    ) -> None:
        BaseManager.__init__(self, sport, data, match, week, odds, predictor)
        TournamentsManagerMixin.__init__(self, tournament, tournament_matches)
        PlayersManagerMixin.__init__(self, player, player_matches)

    async def update_matches_for_year(self) -> list[MatchSDM]:
        raise NotImplementedError()
