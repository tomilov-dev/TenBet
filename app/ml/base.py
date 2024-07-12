import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from model.prediction import MatchPredictionHA, MatchPrediction1x2
from manager.base import BasePredictorInterface, BaseDataInterface
from manager.service import SportType


class BasePreditor(BasePredictorInterface):
    def __init__(
        self,
        sport: SportType,
        data: BaseDataInterface,
    ) -> None:
        self.sport = sport
        self.data = data
