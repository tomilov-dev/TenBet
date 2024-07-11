import sys
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from pymongo.errors import DuplicateKeyError

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from manager.base import (
    BaseManager,
    BaseDataInterface,
    TournamentsManagerMixin,
    PlayersManagerMixin,
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


class TennisMenDataInterface(BaseDataInterface):
    pass


class TennisMenManager(
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
    ) -> None:
        BaseManager.__init__(self, sport, data, match, week, odds)
        TournamentsManagerMixin.__init__(self, tournament, tournament_matches)
        PlayersManagerMixin.__init__(self, player, player_matches)
