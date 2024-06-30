import re
import sys
import asyncio
from pprint import pprint
from pathlib import Path
from bs4 import BeautifulSoup as soup
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PROJ_DIR = ROOT_DIR.parent
sys.path.append(str(ROOT_DIR))
sys.path.append(str(PROJ_DIR))


from models import WeekTournament, WeekMatch
from flashscore.common import FlashScoreScraper, SportType, SPORT, StatusCode


STATUS_RX = re.compile(r"¬AC÷(\d+)¬")

### Day Codes
LAST_WEEK_DAYS = [
    -7,
    -6,
    -5,
    -4,
    -3,
    -2,
    -1,
    0,
]  # 0 because today can be some finished matches
FUTURE_DAYS = [0, 1]
YESTERDAY_DAYS = [-1]


class WeeklyMatchesScraper(FlashScoreScraper):
    def __init__(
        self,
        proxy: str = None,
        debug: bool = False,
        sport: SportType = SPORT.TENNIS_MEN,
    ) -> None:
        super().__init__(proxy, debug, sport)

    def parse_day(self, response: str) -> list[WeekTournament]:
        week_tournaments: list[WeekTournament] = []

        raw_tournament_data = []
        raw_tournaments = response.split("~ZA÷")[1:]
        for raw_tournament in raw_tournaments:
            raw_tournament_data.append(raw_tournament)

        for tournament in raw_tournament_data:
            tournament_name = tournament.split("¬ZEE÷")[0]
            matches: list[WeekMatch] = []

            raw_matches = tournament.split("¬~AA÷")[1:]
            for raw_match in raw_matches:
                code = raw_match.split("¬AD÷")[0]
                date = raw_match.split("¬AD÷")[1].split("¬ADE÷")[0]
                status = StatusCode.extract(STATUS_RX, raw_match)

                match = WeekMatch(code=code, date=int(date), status=status)
                matches.append(match)

            tournament = WeekTournament(name=tournament_name, matches=matches)
            week_tournaments.append(tournament)

        return week_tournaments

    async def scrape_day(self, day: int) -> list[WeekTournament]:
        page = "0" if day == 0 else f"{day}"
        url = f"https://d.flashscore.co.uk/x/feed/{self.sport.week_prefix}_{page}_5_en-uk_1"

        response = await self.request(url)
        if response is None:
            return []

        return self.parse_day(response)

    async def scrape(self, days: list[int]) -> list[WeekTournament]:
        tasks = [asyncio.create_task(self.scrape_day(d)) for d in days]
        week_tournaments = await asyncio.gather(*tasks)
        week_tournaments = [wt for sub in week_tournaments for wt in sub]
        return week_tournaments


async def test():
    scraper = WeeklyMatchesScraper()

    week_tournaments = await scraper.scrape(FUTURE_DAYS)
    print(week_tournaments)


if __name__ == "__main__":
    asyncio.run(test())
