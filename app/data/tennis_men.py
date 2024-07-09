import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from data.base import RepositoryInterface


class TennisMenRepositoryInterface(RepositoryInterface):
    pass
