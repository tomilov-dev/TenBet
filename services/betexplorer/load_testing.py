import json
import asyncio
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio

from scraper import BetExplorerScraper

DIR = Path(__file__).parent


class LoadTesting:
    def __init__(self):
        self.scraper = BetExplorerScraper()

    def upload_codes(self) -> list[str]:
        with open(DIR / "match_codes.json", "r") as file:
            data = json.loads(file.read())
            return [m["code"] for m in data]

    async def run(self):
        codes = self.upload_codes()
        codes = codes[:1000]

        tasks = [asyncio.create_task(self.scraper.scrape(code)) for code in codes]
        print("Collect matches odds")
        match_odds = await tqdm_asyncio.gather(*tasks)


if __name__ == "__main__":
    lt = LoadTesting()
    asyncio.run(lt.run())
