import sys
from pathlib import Path
from abc import ABC, abstractmethod

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))
from model.service import MatchSDM
from model.domain import MatchStatusDTO
from model.prediction import MatchPredictionHA, MatchPrediction1x2
from manager.base import BaseDataInterface, MatchFilter


class RepositoryInterface(ABC):
    ### MATCH collection methods
    @abstractmethod
    async def find_code(self, code: str) -> dict:
        pass

    @abstractmethod
    async def find_codes(self, codes: list[str]) -> list[dict]:
        pass

    @abstractmethod
    async def add_prediction(self, code: str, prediction: dict) -> None:
        pass

    @abstractmethod
    async def get_prediction(self, code: str) -> dict:
        pass

    @abstractmethod
    async def add_match(self, match: dict) -> None:
        pass

    @abstractmethod
    async def add_matches(self, matches: list[dict]) -> None:
        pass

    @abstractmethod
    async def get_match(self, code: str) -> dict | None:
        pass

    @abstractmethod
    async def get_matches(self, codes: list[str]) -> list[dict] | None:
        pass

    @abstractmethod
    async def get_filtered_matches(
        self,
        match_filter: dict,
        limit: int | None = None,
        skip: int | None = None,
    ) -> list[dict] | None:
        pass

    ### CURRENT collection methods
    @abstractmethod
    async def upsert_current_match(self, match: dict) -> None:
        pass

    @abstractmethod
    async def upsert_current_matches(self, matches: list[dict]) -> None:
        pass

    @abstractmethod
    async def get_current_match(self, code: str) -> dict | None:
        pass

    @abstractmethod
    async def get_current_matches(self, codes: list[str]) -> list[dict] | None:
        pass

    @abstractmethod
    async def get_all_current_matches(self) -> list[dict] | None:
        pass

    @abstractmethod
    async def get_current_codes(self) -> list[dict] | None:
        pass

    @abstractmethod
    async def delete_current_match(self, code: str) -> None:
        pass

    @abstractmethod
    async def delete_current_matches(self, codes: list[str]) -> None:
        pass


class BaseData(BaseDataInterface):
    def __init__(self, db: RepositoryInterface) -> None:
        self.db = db

    async def find_code(self, code: str) -> MatchStatusDTO:
        code = await self.db.find_code(code)
        code = MatchStatusDTO(**code) if code else None
        return code

    async def find_codes(self, codes: list[str]) -> list[MatchStatusDTO]:
        codes = await self.db.find_codes(codes)
        codes = [MatchStatusDTO(**c) for c in codes]
        return codes

    async def add_prediction(
        self,
        prediction: MatchPredictionHA | MatchPrediction1x2,
    ) -> None:
        return await self.db.add_prediction(
            code=prediction.code,
            prediction=prediction.model_dump(),
        )

    async def get_prediction(
        self,
        code: str,
    ) -> MatchPredictionHA | MatchPrediction1x2:
        prediction = await self.db.get_prediction(code)
        return MatchPredictionHA(**prediction)

    async def add_match(self, match: MatchSDM) -> None:
        await self.db.add_match(match.model_dump())

    async def add_matches(self, matches: list[MatchSDM]) -> None:
        if not matches:
            return None
        await self.db.add_matches([match.model_dump() for match in matches])

    async def get_match(self, code: str) -> MatchSDM | None:
        match = await self.db.get_match(code)
        match = MatchSDM(**match) if match else None
        return match

    async def get_matches(self, codes: list[str]) -> list[MatchSDM] | None:
        matches = await self.db.get_matches(codes)
        matches = [MatchSDM(**m) for m in matches]
        return matches

    async def get_filtered_matches(
        self,
        match_filter: MatchFilter,
        limit: int | None = None,
        skip: int | None = None,
    ) -> list[MatchSDM] | None:
        """Return filtered and sorted matches"""

        filters = match_filter.dump()
        matches = await self.db.get_filtered_matches(filters, limit, skip)
        return [MatchSDM(**m) for m in matches]

    async def upsert_current_match(self, match: MatchSDM) -> None:
        await self.db.upsert_current_match(match.model_dump())

    async def upsert_current_matches(self, matches: list[MatchSDM]) -> None:
        if not matches:
            return None
        await self.db.upsert_current_matches([match.model_dump() for match in matches])

    async def get_current_match(self, code: str) -> MatchSDM | None:
        current = await self.db.get_current_match(code)
        current = MatchSDM(**current) if current else None
        return current

    async def get_current_matches(self, codes: list[str]) -> list[MatchSDM] | None:
        currents = await self.db.get_current_matches(codes)
        currents = [MatchSDM(**current) for current in currents]
        return currents

    async def get_all_current_matches(self) -> list[MatchSDM] | None:
        currents = await self.db.get_all_current_matches()
        currents = [MatchSDM(**current) for current in currents]
        return currents

    async def get_current_codes(self) -> list[MatchStatusDTO] | None:
        currents = await self.db.get_current_codes()
        currents = [MatchStatusDTO(**f) for f in currents]
        return currents

    async def delete_current_match(self, code: str) -> None:
        await self.db.delete_current_match(code)

    async def delete_current_matches(self, codes: list[str]) -> None:
        await self.db.delete_current_matches(codes)
