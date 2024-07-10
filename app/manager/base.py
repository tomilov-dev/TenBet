import sys
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from model.service import MatchSDM
from model.domain import MatchStatusDTO
from manager.service import (
    SportType,
    FlashScoreMatchScraperInterface,
    BetExplorerScraperInterface,
    FlashScoreTournamentScraperInterface,
    FlashScoreTournamentMatchesScraperIntefrace,
    FlashScoreWeeklyMatchesScraper,
    FlashScorePlayerScraperInterface,
    FlashScorePlayerMatchesScraperInterface,
    FUTURE_DAYS,
)


class BaseDataInterface(ABC):
    @abstractmethod
    async def add_match(self, match: MatchSDM) -> None:
        pass

    @abstractmethod
    async def add_matches(self, matches: list[MatchSDM]) -> None:
        pass

    @abstractmethod
    async def find_code(self, code: str) -> MatchStatusDTO:
        pass

    @abstractmethod
    async def find_codes(self, codes: list[str]) -> list[MatchStatusDTO]:
        pass


class BaseManager:
    def __init__(
        self,
        sport: SportType,
        data: BaseDataInterface,
        match: FlashScoreMatchScraperInterface,
        week: FlashScoreWeeklyMatchesScraper,
        odds: BetExplorerScraperInterface,
    ) -> None:
        self.sport = sport
        self.data = data

        self.match = match
        self.week = week
        self.odds = odds

    async def find_code(self, code: str) -> MatchSDM | None:
        """Return match code and status if exists in the database"""
        return await self.data.find_code(code)

    async def find_codes(self, codes: list[str]) -> list[dict]:
        """Return match codes and statuses if codes exists in the database"""
        return await self.data.find_codes(codes)

    async def upsert_match(self, code: str) -> MatchSDM | None:
        raise NotImplementedError("Future method")

    async def add_match(self, code: str) -> MatchSDM | None:
        found = await self.find_code(code)
        if found:
            return None

        match_data = await self.match.scrape(code)
        odds_data = await self.odds.scrape(code)
        match_data.odds = odds_data

        await self.data.add_match(match_data)
        return match_data

    async def add_matches(self, codes: list[str]) -> list[MatchSDM] | None:
        tasks = [asyncio.create_task(self.add_match(code)) for code in codes]
        matches = await asyncio.gather(*tasks)
        return [m for m in matches if m is not None]

    async def collect_future_matches(self):
        matches = await self.week.scrape(FUTURE_DAYS)
        return matches

    async def update_matches_for_week(self):
        pass

    async def update_matches_for_year(self):
        pass


class TournamentsManagerMixin:
    def __init__(
        self,
        tournament: FlashScoreTournamentScraperInterface,
        tournament_matches: FlashScoreTournamentMatchesScraperIntefrace,
    ) -> None:
        self.tournament = tournament
        self.tournament_matches = tournament_matches

    async def collect_tournaments_matches(self):
        pass


class PlayersManagerMixin:
    def __init__(
        self,
        player: FlashScorePlayerScraperInterface,
        player_matches: FlashScorePlayerMatchesScraperInterface,
    ) -> None:
        self.player = player
        self.player_matches = player_matches

    async def collect_players_matches(self):
        pass
