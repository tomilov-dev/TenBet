import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from settings import settings
from db.core import client
from db.api.tennis_men import TennisMenRepository


async def test():
    code = "K831uSar"
    api = TennisMenRepository()

    code = await api.find_code(code=code)
    print(code)


if __name__ == "__main__":
    asyncio.run(test())
