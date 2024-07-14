import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from model.service import MatchSDM
from model.prediction import MatchPredictionHA
from manager.tennis_women import TennisWomenDataInterface
from manager.service import SPORT
from ml.base import StandardML, StandardMLTrainer, StandardPredictor, TMP_MONTH


class StandardTennisWomenML(StandardML):
    DIST_DIR = Path(__file__).parent / "assets" / "standard"
    TIME_SPREAD = TMP_MONTH * 6
    MODEL_NAME = "Standard Tennis Women Model"

    def __init__(
        self,
        data: TennisWomenDataInterface,
    ) -> None:
        StandardML.__init__(self, sport=SPORT.TENNIS_WOMEN, data=data)


class StandardTennisWomenMLTrainer(
    StandardTennisWomenML,
    StandardMLTrainer,
):
    pass


class StandardTennisWomenMLPredictor(
    StandardTennisWomenML,
    StandardPredictor,
):
    def __init__(self, data: TennisWomenDataInterface) -> None:
        StandardTennisWomenML.__init__(self, data=data)
        StandardPredictor.__init__(self, sport=SPORT.TENNIS_WOMEN, data=data)
