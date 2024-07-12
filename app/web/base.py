from fastapi import APIRouter, HTTPException

from manager.base import BaseManager
from model.service import MatchSDM
from model.prediction import MatchPredictionHA, MatchPrediction1x2


class BaseRouter:
    def __init__(
        self,
        router: APIRouter,
        manager: BaseManager,
    ) -> None:
        self.router = router
        self.manager = manager

        self.router.add_api_route(
            "/match/{code}",
            self.get_match,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/predict/{code}",
            self.get_prediction,
            methods=["GET"],
        )
        self.router.add_api_route(
            "/current-matches",
            self.get_current_matches,
            methods=["GET"],
        )

    async def get_match(self, code: str) -> MatchSDM:
        match = await self.manager.get_match(code)
        if not match:
            raise HTTPException(404, "Match was not found")

        return match

    async def get_prediction(self, code: str) -> MatchPredictionHA | MatchPrediction1x2:
        prediction = await self.manager.get_prediction(code)
        return prediction

    async def get_current_matches(self) -> list[MatchSDM]:
        matches = await self.manager.get_all_current_matches()
        return matches
