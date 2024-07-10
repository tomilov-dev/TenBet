import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from data.base import RepositoryInterface, BaseData
from manager.tennis_men import TennisMenDataInterface


class TennisMenRepositoryInterface(RepositoryInterface):
    pass


class TennisMenData(
    BaseData,
    TennisMenDataInterface,
):
    pass
