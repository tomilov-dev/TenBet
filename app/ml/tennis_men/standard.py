import os
import sys
import pickle
import asyncio
import bisect
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

from db.api.tennis_men import TennisMenRepository
from data.tennis_men import TennisMenData
from manager.service import SPORT, SportType
from manager.base import MatchFilter
from model.service import MatchSDM

from ml.base import StandardML, StandardMLTrainer, StandardPredictor


class StandardTennisMenML(StandardML):
    DIST_DIR = Path(__file__).parent / "assets" / "standard"


class StandardTennisMenMLTrainer(
    StandardTennisMenML,
    StandardMLTrainer,
):
    pass


class StandardTennisMenMLPredictor(
    StandardTennisMenML,
    StandardPredictor,
):
    pass


DIST_DIR = Path(__file__).parent / "assets" / "standard"


async def train():
    trainer = StandardTennisMenMLTrainer(
        SPORT.TENNIS_MEN,
        data=TennisMenData(TennisMenRepository()),
    )

    await trainer.train(preprocessed_features=True)


async def test_model():
    data = TennisMenData(TennisMenRepository())
    match = await data.get_match("WGndc4yp")

    predictor = StandardTennisMenMLPredictor(
        SPORT.TENNIS_MEN,
        data=data,
    )

    predict = await predictor.predict(match)
    print(predict)


if __name__ == "__main__":
    # asyncio.run(train())
    asyncio.run(test_model())
