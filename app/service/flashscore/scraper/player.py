import re
import sys
import asyncio
from pprint import pprint
from pathlib import Path
from bs4 import BeautifulSoup as soup


ROOT_DIR = Path(__file__).parent.parent.parent.parent
sys.path.append(str(ROOT_DIR))


from model.service import PlayerSDM, MatchCodeSDM
from service.flashscore.common import FlashScoreScraper, SportType, SPORT
from manager.service import (
    FlashScorePlayerScraperInterface,
    FlashScorePlayerMatchesScraperInterface,
)


class PlayerScraper(FlashScorePlayerScraperInterface, FlashScoreScraper):
    """Scrape players from rank"""

    def __init__(
        self,
        sport: SportType,
        proxy: str = None,
        debug: bool = False,
    ) -> None:
        FlashScorePlayerScraperInterface.__init__(self, sport)
        FlashScoreScraper.__init__(self, proxy, debug)

    def parse(self, response: str) -> list[PlayerSDM]:
        content = response.split("¬PT÷PN¬PV÷")[1:]

        players: list[PlayerSDM] = []
        for element in content:
            name = element.split("¬PT÷PI¬PV÷")[0]
            player_id = element.split("¬PT÷CI¬PV÷")[0].split("¬PT÷PI¬PV÷")[1]
            country = element.split("¬PT÷RA¬PV÷")[0].split("¬PT÷CN¬PV÷")[1]
            rank = element.split("¬PT÷RA¬PV÷")[1].split("¬PT÷RAP¬PV÷")[0]
            player_link = element.split("¬PT÷PU¬PV÷")[1].split("¬PT÷TP¬PV÷")[0]
            country_id = element.split("¬PT÷CI¬PV÷")[1].split("¬PT÷CN¬PV÷")[0]

            player = PlayerSDM(
                id=player_id,
                name=name,
                country=country,
                country_id=country_id,
                rank=rank,
                link=player_link,
            )
            players.append(player)

        return players

    async def scrape(self, rank_url: str) -> list[PlayerSDM]:
        response = await self.request(rank_url)
        if response is None:
            return []

        players = self.parse(response)
        return players


class PlayerMatchesParser:
    def __init__(self, sport: SportType):
        self.sport = sport

    def parse_page(self, response: str) -> list[MatchCodeSDM]:
        matches: list[MatchCodeSDM] = []
        matches_data, headers = [], []

        tournaments = response.split("~ZA÷")[1:]
        for tour in tournaments:
            el = tour.split("¬~AA÷")
            headers.extend([el[0]]), matches_data.extend(el[1:])

        for index in range(len(matches_data)):
            match: str = matches_data[index]
            date = match.split("¬AD÷")[1].split("¬ADE÷")[0]
            code = match.split("¬AD÷")[0]

            matches.append(MatchCodeSDM(date=date, code=code))

        return matches


class PlayerMatchesScaper(FlashScorePlayerMatchesScraperInterface, FlashScoreScraper):
    """Scrape matches from player page"""

    def __init__(
        self,
        sport: SportType,
        proxy: str = None,
        debug: bool = False,
    ) -> None:
        FlashScorePlayerMatchesScraperInterface.__init__(self, sport)
        FlashScoreScraper.__init__(self, proxy, debug)

        self.parser = PlayerMatchesParser(sport)

    def create_urls(self, player: PlayerSDM, page_limit: int) -> list[str]:
        cid = player.country_id
        pid = player.id

        urls = [
            f"https://d.flashscore.co.uk/x/feed/{self.sport.prefix}_{cid}_{pid}_{pg}_5_en-uk_1_s"
            for pg in range(page_limit)
        ]

        return urls

    async def scrape_page(self, url: str) -> list[MatchCodeSDM]:
        response = await self.request(url)
        if response is None:
            return []

        matches = self.parser.parse_page(response)
        return matches

    async def scrape(
        self,
        player: PlayerSDM,
        page_limit: int = 1,
    ) -> list[MatchCodeSDM]:
        urls = self.create_urls(player, page_limit)

        tasks = [asyncio.create_task(self.scrape_page(url)) for url in urls]
        matches = await asyncio.gather(*tasks)
        matches = [match for sublist in matches for match in sublist]

        return matches


async def test_player_match_scraper():
    rank_url = "https://d.flashscore.co.uk/x/feed/ran_dSJr14Y8_1"

    player_scraper = PlayerScraper(sport=SPORT.TENNIS_MEN)
    scraper = PlayerMatchesScaper(sport=SPORT.TENNIS_MEN)

    players = await player_scraper.scrape(rank_url)
    # print(players)

    matches = await scraper.scrape(players[0], 2)
    print(matches)


if __name__ == "__main__":
    asyncio.run(test_player_match_scraper())
