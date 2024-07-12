import sys
import random
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from manager.base import BaseDataInterface
from manager.service import SPORT
from ml.base import BasePreditor, MatchPrediction1x2, MatchPredictionHA


class RandomTennisMenPredictor(BasePreditor):
    def __init__(self, data: BaseDataInterface) -> None:
        super().__init__(SPORT.TENNIS_MEN, data)

    async def predict(self, code: str) -> MatchPredictionHA:
        proba = random.random()
        winner = 1 if proba >= 0.5 else 0
        return MatchPredictionHA(
            code=code,
            win_predict=winner,
            probability_t1=proba,
            probability_t2=1 - proba,
        )
