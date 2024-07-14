import sys
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent
sys.path.append(str(ROOT_DIR))

from data.tennis_women import TennisWomenData
from db.api.tennis_women import TennisWomenRepository
from ml.tennis_women.standard import (
    StandardTennisWomenMLTrainer,
    StandardTennisWomenMLPredictor,
)


async def train():
    trainer = StandardTennisWomenMLTrainer(
        data=TennisWomenData(TennisWomenRepository()),
    )

    await trainer.train(preprocessed_features=False)


async def test_model():
    data = TennisWomenData(TennisWomenRepository())
    match = await data.get_match("Yq5BO72S")

    predictor = StandardTennisWomenMLPredictor(
        data=data,
    )

    predict = await predictor.predict(match)
    print(predict)


if __name__ == "__main__":
    # asyncio.run(train())
    asyncio.run(test_model())
