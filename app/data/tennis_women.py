import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from data.base import RepositoryInterface, BaseData
from manager.tennis_women import TennisWomenDataInterface


class TennisWomenRepositoryInterface(RepositoryInterface):
    pass


class TennisWomenData(
    BaseData,
    TennisWomenDataInterface,
):
    pass
