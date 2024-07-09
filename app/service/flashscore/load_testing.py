import json
import asyncio
from tqdm.asyncio import tqdm_asyncio

from scraper.player import PlayerScraper, PlayerMatchesScaper
from scraper.tournament import TournamentMatchesScraper, TournamentScraper
from scraper.match import MatchScraper
from scraper.week import WeeklyMatchesScraper
from app.model.service import MatchCodeSDM
from common import SportType, SPORT


class LoadTesting:
    def __init__(self, sport: SportType = SPORT.TENNIS_MEN) -> None:
        self.sport = sport

        self.tournament_scraper = TournamentScraper(sport=sport)
        self.tournament_matches_scraper = TournamentMatchesScraper(sport=sport)

        self.match_scraper = MatchScraper(sport=sport)

    async def get_matches(self) -> list[MatchCodeSDM]:
        category_url = "https://www.flashscore.co.uk/x/req/m_2_5724"

        print("Collect tournaments")
        tournaments = await self.tournament_scraper.scrape(category_url)
        turls = [t.by_year_urls[: min(5, len(t.by_year_urls))] for t in tournaments]
        urls = list(set([url for sub in turls for url in sub]))

        print("Collect tournaments matches")
        tasks = [
            asyncio.create_task(self.tournament_matches_scraper.scrape(url))
            for url in urls
        ]
        matches = await tqdm_asyncio.gather(*tasks)
        matches = [m for sub in matches for m in sub]

        return matches

    async def run(self) -> None:
        match_codes = await self.get_matches()

        # with open("match_codes.json", "w") as file:
        #     json.dump([m.model_dump() for m in match_codes], file)

        match_codes = match_codes[:1000]

        tasks = [
            asyncio.create_task(self.match_scraper.scrape(m.code)) for m in match_codes
        ]

        print("Collect matches data")
        matches = await tqdm_asyncio.gather(*tasks)
        print(matches)


if __name__ == "__main__":
    lt = LoadTesting()
    asyncio.run(lt.run())
