import sys
from pathlib import Path
from abc import ABC, abstractmethod

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))
from model.service import MatchSDM
from model.domain import MatchStatusDTO
from manager.base import BaseDataInterface


class RepositoryInterface(ABC):
    @abstractmethod
    async def add_match(self, match: dict) -> None:
        pass

    @abstractmethod
    async def add_matches(self, matches: list[dict]) -> None:
        pass

    @abstractmethod
    async def find_code(self, code: str) -> dict:
        pass

    @abstractmethod
    async def find_codes(self, codes: list[str]) -> list[dict]:
        pass


class BaseData(BaseDataInterface):
    def __init__(self, db: RepositoryInterface) -> None:
        self.db = db

    async def add_match(self, match: MatchSDM) -> None:
        await self.db.add_match(match.model_dump())

    async def add_matches(self, matches: list[MatchSDM]) -> None:
        await self.db.add_matches([match.model_dump() for match in matches])

    async def find_code(self, code: str) -> MatchStatusDTO:
        return await self.db.find_code(code)

    async def find_codes(self, codes: list[str]) -> list[MatchStatusDTO]:
        return await self.db.find_codes(codes)
