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


from models import Tournament, TournamentByYear, MatchCode
from flashscore.common import FlashScoreScraper, SportType, SPORT


class TournamentScraper(FlashScoreScraper):
    """Scrape tournaments and tournaments archive links from category"""

    def __init__(
        self,
        proxy: str = None,
        debug: bool = False,
        sport: SportType = SPORT.TENNIS_MEN,
    ) -> None:
        super().__init__(proxy, debug, sport)

    def parse_page(self, response: str, tournament: Tournament) -> Tournament:
        tournament_links: list[str] = []

        s = soup(response, "lxml")
        _season = s.find_all("div", {"class": "archive__season"})
        for el in _season:
            i = el.find("a")
            if i is not None:
                link = "https://www.flashscore.co.uk" + i.get("href") + "results/"
                tournament_links.append(link)

        tournament.by_year_urls = tournament_links
        return tournament

    def parse_category(self, response: str) -> list[Tournament]:
        tournaments: list[Tournament] = []
        tour_name = response.split("¬ML÷")[1]
        tour_name = tour_name.split("¬~MN÷")[0].strip()

        raw_tours = response.split("¬~MN÷")[1:]
        for raw_tour in raw_tours:
            tour_nick = raw_tour.split("¬MT÷")[0].split("¬MU÷")[1]
            archive_link = (
                "https://www.flashscore.co.uk/"
                + self.sport.tag
                + "/"
                + tour_name
                + "/"
                + tour_nick
                + "/archive/"
            )

            tournaments.append(
                Tournament(
                    category=tour_name,
                    name=tour_nick,
                    archive_link=archive_link,
                )
            )

        return tournaments

    async def scrape_page(self, tournament: Tournament) -> Tournament:
        """Scrape tournament page"""

        response = await self.request(tournament.archive_link)
        if response is None:
            return tournament

        return self.parse_page(response, tournament)

    async def scrape_category(self, category_url: str) -> list[Tournament]:
        """Scrape category of tournaments or league"""

        response = await self.request(category_url)
        if response is None:
            return []

        tournaments = self.parse_category(response)
        return tournaments

    async def scrape(
        self,
        category_url: str,
        limit: int | None = None,
    ) -> list[Tournament]:
        tournaments = await self.scrape_category(category_url)

        if limit is not None and limit > 0:
            tournaments = tournaments[: min(limit, len(tournaments))]

        tasks = [asyncio.create_task(self.scrape_page(t)) for t in tournaments]
        tournaments = await tqdm_asyncio.gather(*tasks)

        return tournaments


class TournamentMatchesParser:
    def __init__(self, sport: SportType):
        self.sport = sport

    def parse_first(self, response: str) -> tuple[list[MatchCode], TournamentByYear]:
        matches: list[MatchCode] = []

        # 1. Сбор матчей
        match_block = response.split("allEventsCount")[0]
        match_block = match_block.split("initialFeeds['results']")[1]
        raw_matches = match_block.split("¬~AA÷")[1:]

        for raw_match in raw_matches:
            code = raw_match.split("¬AD÷")[0]
            date = raw_match.split("¬AD÷")[1].split("¬ADE÷")[0]

            matches.append(MatchCode(date=date, code=code))

        # 2. Проверка количества матчей
        events_count = response.split("allEventsCount: ")[1]
        events_count = events_count.split(",")[0]
        events_count = int(events_count)

        # 3. Сбор мета-информации
        league_element = response.split('getToggleIcon("')[1]
        league_element = league_element.split('",')[0]

        season_id = response.split("seasonId: ")[1]
        season_id = season_id.split(",")[0]

        tournament = TournamentByYear(
            league=league_element,
            season_id=season_id,
            events_count=events_count,
        )
        tournament.add_codes([m.code for m in matches])

        return matches, tournament

    def parse_other(self, response: str) -> list[MatchCode]:
        codes: list[MatchCode] = []

        raw_matches = response.split("¬~AA÷")[1:]
        for raw_match in raw_matches:
            code = raw_match.split("¬AD÷")[0]
            date = raw_match.split("¬AD÷")[1].split("¬ADE÷")[0]
            codes.append(MatchCode(date=date, code=code))

        return codes


class TournamentMatchesScraper(FlashScoreScraper):
    def __init__(
        self,
        proxy: str = None,
        debug: bool = False,
        sport: SportType = SPORT.TENNIS_MEN,
    ) -> None:
        super().__init__(proxy, debug, sport)

        self.parser = TournamentMatchesParser(sport)

    async def scrape_other(
        self,
        matches: list[MatchCode],
        tournament: TournamentByYear,
    ) -> MatchCode:
        while not tournament.parsed():
            url = tournament.get_url()
            if url is not None:
                response = await self.request(url)
                if response is None:
                    break
                if len(response) == 0:
                    break

                other_matches = self.parser.parse_other(response)
                matches.extend(other_matches)
                tournament.add_codes([m.code for m in other_matches])

        return matches

    async def scrape_first(self, url: str) -> tuple[list[MatchCode], TournamentByYear]:
        response = await self.request(url)
        matches, tournament = self.parser.parse_first(response)
        return matches, tournament

    async def scrape(self, url: str) -> list[MatchCode]:
        matches, tournament = await self.scrape_first(url)
        matches = await self.scrape_other(matches, tournament)
        matches = MatchCode.drop_dups(matches)
        return matches


async def test():
    category_url = "https://www.flashscore.co.uk/x/req/m_2_5724"
    tournament_scraper = TournamentScraper()
    scraper = TournamentMatchesScraper()

    # tournaments = await tournament_scraper.scrape(category_url)

    # url = "https://www.flashscore.co.uk/tennis/atp-singles/australian-open/results/"
    # url = "https://www.flashscore.co.uk/tennis/atp-singles/madrid/results/"
    url = "https://www.flashscore.co.uk/tennis/atp-singles/halle/results/"

    matches = await scraper.scrape(url)
    print(matches)


if __name__ == "__main__":
    asyncio.run(test())
