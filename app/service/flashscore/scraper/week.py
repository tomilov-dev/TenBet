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


from model.service import MatchCodeSDM
from manager.service import FlashScoreWeeklyMatchesScraper, FUTURE_DAYS
from service.flashscore.common import (
    FlashScoreScraper,
    SportType,
    SPORT,
    StatusCode,
    TournamentNameParser,
)


STATUS_CODE_RX = re.compile(r"¬AC÷(\d+)¬")


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

    def parse_day(self, response: str) -> list[MatchCodeSDM]:
        matches: list[MatchCodeSDM] = []

        raw_tournament_data = []
        raw_tournaments = response.split("~ZA÷")[1:]
        for raw_tournament in raw_tournaments:
            raw_tournament_data.append(raw_tournament)

        for tournament in raw_tournament_data:
            tournament_name = tournament.split("¬ZEE÷")[0]
            tournament_name_parsed = TournamentNameParser.parse(tournament_name)

            raw_matches = tournament.split("¬~AA÷")[1:]
            for raw_match in raw_matches:
                code = raw_match.split("¬AD÷")[0]
                date = raw_match.split("¬AD÷")[1].split("¬ADE÷")[0]
                status = StatusCode.extract(STATUS_CODE_RX, raw_match)

                match = MatchCodeSDM(
                    **tournament_name_parsed.model_dump(),
                    code=code,
                    date=int(date),
                    status=status,
                )
                matches.append(match)

        return matches

    async def scrape_day(self, day: int) -> list[MatchCodeSDM]:
        page = "0" if day == 0 else f"{day}"
        url = f"https://d.flashscore.co.uk/x/feed/{self.sport.week_prefix}_{page}_5_en-uk_1"

        response = await self.request(url)
        if response is None:
            return []

        return self.parse_day(response)

    async def scrape(self, days: list[int]) -> list[MatchCodeSDM]:
        tasks = [asyncio.create_task(self.scrape_day(d)) for d in days]

        week_matches = await asyncio.gather(*tasks)
        week_matches = [wt for sub in week_matches for wt in sub]
        return week_matches


async def test():
    scraper = WeeklyMatchesScraper(sport=SPORT.TENNIS_MEN)

    week_matches = await scraper.scrape(FUTURE_DAYS)
    print(week_matches[0])


if __name__ == "__main__":
    asyncio.run(test())
