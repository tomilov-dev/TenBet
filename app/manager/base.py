import sys
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from model.service import MatchSDM
from model.domain import MatchStatusDTO
from manager.service import SportType
from manager.service import (
    FlashScoreMatchScraperInterface,
    BetExplorerScraperInterface,
    FlashScoreTournamentScraperInterface,
    FlashScoreTournamentMatchesScraperIntefrace,
    FlashScoreWeeklyMatchesScraper,
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
        odds: BetExplorerScraperInterface,
        tournament: FlashScoreTournamentScraperInterface,
        tournament_matches: FlashScoreTournamentMatchesScraperIntefrace,
        week: FlashScoreWeeklyMatchesScraper,
    ):
        self.sport = sport
        self.data = data

        self.match = match
        self.odds = odds
        self.tournament = tournament
        self.tournament_matches = tournament_matches
        self.week = week

    async def find_code(self, code: str) -> MatchSDM | None:
        """Return match code and status if exists in the database"""
        return await self.data.find_code(code)

    async def find_codes(self, codes: list[str]) -> list[dict]:
        """Return match codes and statuses if codes exists in the database"""
        return await self.data.find_codes(codes)

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
