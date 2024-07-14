import sys
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent.parent
sys.path.append(str(ROOT_DIR))

from data.tennis_men import TennisMenData
from db.api.tennis_men import TennisMenRepository
from ml.tennis_men.standard import (
    StandardTennisMenMLTrainer,
    StandardTennisMenMLPredictor,
)


async def train():
    trainer = StandardTennisMenMLTrainer(
        data=TennisMenData(TennisMenRepository()),
    )

    await trainer.train(preprocessed_features=True)


async def test_model():
    data = TennisMenData(TennisMenRepository())
    match = await data.get_match("WGndc4yp")

    predictor = StandardTennisMenMLPredictor(data=data)

    predict = await predictor.predict(match)
    print(predict)


if __name__ == "__main__":
    # asyncio.run(train())
    asyncio.run(test_model())
