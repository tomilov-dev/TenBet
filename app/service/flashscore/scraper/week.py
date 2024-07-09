import re
import sys
import asyncio
from pprint import pprint
from pathlib import Path
from bs4 import BeautifulSoup as soup
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio


ROOT_DIR = Path(__file__).parent.parent.parent.parent
sys.path.append(str(ROOT_DIR))


from model.service import WeekTournamentSDM, WeekMatchSDM
from service.flashscore.common import FlashScoreScraper, SportType, SPORT, StatusCode
from manager.service import FlashScoreWeeklyMatchesScraper, FUTURE_DAYS


STATUS_RX = re.compile(r"¬AC÷(\d+)¬")


class WeeklyMatchesScraper(
    FlashScoreWeeklyMatchesScraper,
    FlashScoreScraper,
):
    def __init__(
        self,
        sport: SportType,
        proxy: str = None,
        debug: bool = False,
    ) -> None:
        FlashScoreWeeklyMatchesScraper.__init__(self, sport)
        FlashScoreScraper.__init__(self, proxy, debug)

    def parse_day(self, response: str) -> list[WeekTournamentSDM]:
        week_tournaments: list[WeekTournamentSDM] = []

        raw_tournament_data = []
        raw_tournaments = response.split("~ZA÷")[1:]
        for raw_tournament in raw_tournaments:
            raw_tournament_data.append(raw_tournament)

        for tournament in raw_tournament_data:
            tournament_name = tournament.split("¬ZEE÷")[0]
            matches: list[WeekMatchSDM] = []

            raw_matches = tournament.split("¬~AA÷")[1:]
            for raw_match in raw_matches:
                code = raw_match.split("¬AD÷")[0]
                date = raw_match.split("¬AD÷")[1].split("¬ADE÷")[0]
                status = StatusCode.extract(STATUS_RX, raw_match)

                match = WeekMatchSDM(code=code, date=int(date), status=status)
                matches.append(match)

            tournament = WeekTournamentSDM(name=tournament_name, matches=matches)
            week_tournaments.append(tournament)

        return week_tournaments

    async def scrape_day(self, day: int) -> list[WeekTournamentSDM]:
        page = "0" if day == 0 else f"{day}"
        url = f"https://d.flashscore.co.uk/x/feed/{self.sport.week_prefix}_{page}_5_en-uk_1"

        response = await self.request(url)
        if response is None:
            return []

        return self.parse_day(response)

    async def scrape(self, days: list[int]) -> list[WeekTournamentSDM]:
        tasks = [asyncio.create_task(self.scrape_day(d)) for d in days]
        week_tournaments = await asyncio.gather(*tasks)
        week_tournaments = [wt for sub in week_tournaments for wt in sub]
        return week_tournaments


async def test():
    scraper = WeeklyMatchesScraper(sport=SPORT.TENNIS_MEN)

    week_tournaments = await scraper.scrape(FUTURE_DAYS)
    print(week_tournaments)


if __name__ == "__main__":
    asyncio.run(test())
