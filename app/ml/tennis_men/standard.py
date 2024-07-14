import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from model.service import MatchSDM
from model.prediction import MatchPredictionHA
from manager.tennis_men import TennisMenDataInterface
from manager.service import SPORT
from ml.base import StandardML, StandardMLTrainer, StandardPredictor, TMP_MONTH


class StandardTennisMenML(StandardML):
    DIST_DIR = Path(__file__).parent / "assets" / "standard"
    TIME_SPREAD = TMP_MONTH * 6
    MODEL_NAME = "Standard Tennis Men Model"

    def __init__(
        self,
        data: TennisMenDataInterface,
    ) -> None:
        StandardML.__init__(self, sport=SPORT.TENNIS_MEN, data=data)


class StandardTennisMenMLTrainer(
    StandardTennisMenML,
    StandardMLTrainer,
):
    pass


class StandardTennisMenMLPredictor(
    StandardTennisMenML,
    StandardPredictor,
):
    def __init__(self, data: TennisMenDataInterface) -> None:
        StandardTennisMenML.__init__(self, data=data)
        StandardPredictor.__init__(self, sport=SPORT.TENNIS_MEN, data=data)
