import sys
import random
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from manager.base import BaseDataInterface
from manager.service import SPORT
from model.service import MatchSDM
from ml.base import RandomPredictor, MatchPrediction1x2, MatchPredictionHA


class RandomTennisMenPredictor(RandomPredictor):
    def __init__(self, data: BaseDataInterface) -> None:
        super().__init__(SPORT.TENNIS_MEN, data)

    async def predict(self, match: MatchSDM) -> MatchPredictionHA:
        proba = random.random()
        winner = 1 if proba >= 0.5 else 2
        return MatchPredictionHA(
            code=match.code,
            win_predict=winner,
            probability_t1=proba,
            probability_t2=1 - proba,
            model="Random Tennis Men Model",
        )
