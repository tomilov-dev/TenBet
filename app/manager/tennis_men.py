import sys
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from pymongo.errors import DuplicateKeyError

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from manager.base import BaseManager, BaseDataInterface


class TennisMenDataInterface(BaseDataInterface):
    pass


class TennisMenManager(BaseManager):
    pass
