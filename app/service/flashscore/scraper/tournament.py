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


from model.service import TournamentSDM, TournamentByYearSDM, MatchCodeSDM
from service.flashscore.common import (
    FlashScoreScraper,
    SportType,
    SPORT,
    StatusCode,
    TournamentNameParser,
)
from manager.service import (
    FlashScoreTournamentScraperInterface,
    FlashScoreTournamentMatchesScraperIntefrace,
)

STATUS_CODE_RX = re.compile("¬AC÷(\d+)¬")


class TournamentScraper(
    FlashScoreTournamentScraperInterface,
    FlashScoreScraper,
):
    """Scrape tournaments and tournaments archive links from category"""

    def __init__(
        self,
        sport: SportType,
        proxy: str = None,
        debug: bool = False,
    ) -> None:
        FlashScoreTournamentMatchesScraperIntefrace.__init__(self, sport)
        FlashScoreScraper.__init__(self, proxy, debug)

    def parse_page(self, response: str, tournament: TournamentSDM) -> TournamentSDM:
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

    def parse_category(self, response: str) -> list[TournamentSDM]:
        tournaments: list[TournamentSDM] = []
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
                TournamentSDM(
                    category=tour_name,
                    name=tour_nick,
                    archive_link=archive_link,
                )
            )

        return tournaments

    async def scrape_page(self, tournament: TournamentSDM) -> TournamentSDM:
        """Scrape tournament page"""

        response = await self.request(tournament.archive_link)
        if response is None:
            return tournament

        return self.parse_page(response, tournament)

    async def scrape_category(self, category_url: str) -> list[TournamentSDM]:
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
    ) -> list[TournamentSDM]:
        tournaments = await self.scrape_category(category_url)
        if limit is not None and limit > 0:
            tournaments = tournaments[: min(limit, len(tournaments))]

        tasks = [asyncio.create_task(self.scrape_page(t)) for t in tournaments]
        tournaments = await tqdm_asyncio.gather(*tasks)

        return tournaments


class TournamentMatchesParser:
    def __init__(self, sport: SportType):
        self.sport = sport

    def parse_first(
        self, response: str
    ) -> tuple[list[MatchCodeSDM], TournamentByYearSDM]:
        matches: list[MatchCodeSDM] = []

        # 1. Сбор матчей
        match_block = response.split("allEventsCount")[0]
        match_block = match_block.split("initialFeeds['results']")[1]
        raw_matches = match_block.split("¬~AA÷")[1:]

        tournament_fullname = match_block.split("¬~ZA÷")[1]
        tournament_fullname = tournament_fullname.split("¬ZEE÷")[0]
        tournament_name_parsed = TournamentNameParser.parse(tournament_fullname)

        for raw_match in raw_matches:
            code = raw_match.split("¬AD÷")[0]
            date = raw_match.split("¬AD÷")[1].split("¬ADE÷")[0]
            status = StatusCode.extract(STATUS_CODE_RX, raw_match)

            matches.append(
                MatchCodeSDM(
                    **tournament_name_parsed.model_dump(),
                    date=date,
                    code=code,
                    status=status,
                )
            )

        # 2. Проверка количества матчей
        events_count = response.split("allEventsCount: ")[1]
        events_count = events_count.split(",")[0]
        events_count = int(events_count)

        # 3. Сбор мета-информации
        league_element = response.split('getToggleIcon("')[1]
        league_element = league_element.split('",')[0]

        season_id = response.split("seasonId: ")[1]
        season_id = season_id.split(",")[0]

        tournament = TournamentByYearSDM(
            league=league_element,
            season_id=season_id,
            events_count=events_count,
        )
        tournament.add_codes([m.code for m in matches])

        return matches, tournament

    def parse_other(self, response: str) -> list[MatchCodeSDM]:
        codes: list[MatchCodeSDM] = []

        tournament_fullname = response.split("¬~ZA÷")[1]
        tournament_fullname = tournament_fullname.split("¬ZEE÷")[0]
        tournament_name_parsed = TournamentNameParser.parse(tournament_fullname)

        raw_matches = response.split("¬~AA÷")[1:]
        for raw_match in raw_matches:
            code = raw_match.split("¬AD÷")[0]
            date = raw_match.split("¬AD÷")[1].split("¬ADE÷")[0]
            status = StatusCode.extract(STATUS_CODE_RX, raw_match)

            codes.append(
                MatchCodeSDM(
                    **tournament_name_parsed.model_dump(),
                    date=date,
                    code=code,
                    status=status,
                )
            )

        return codes


class TournamentMatchesScraper(
    FlashScoreTournamentMatchesScraperIntefrace,
    FlashScoreScraper,
):
    def __init__(
        self,
        sport: SportType,
        proxy: str = None,
        debug: bool = False,
    ) -> None:
        FlashScoreTournamentMatchesScraperIntefrace.__init__(self, sport)
        FlashScoreScraper.__init__(self, proxy, debug)

        self.parser = TournamentMatchesParser(sport)

    async def scrape_other(
        self,
        matches: list[MatchCodeSDM],
        tournament: TournamentByYearSDM,
    ) -> MatchCodeSDM:
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

    async def scrape_first(
        self, url: str
    ) -> tuple[list[MatchCodeSDM], TournamentByYearSDM]:
        response = await self.request(url)
        matches, tournament = self.parser.parse_first(response)
        return matches, tournament

    async def scrape(self, url: str) -> list[MatchCodeSDM]:
        matches, tournament = await self.scrape_first(url)
        matches = await self.scrape_other(matches, tournament)
        matches = MatchCodeSDM.drop_dups(matches)
        return matches


async def test():
    category_url = "https://www.flashscore.co.uk/x/req/m_2_5724"
    tournament_scraper = TournamentScraper(SPORT.TENNIS_MEN)
    scraper = TournamentMatchesScraper(SPORT.TENNIS_MEN)

    # tournaments = await tournament_scraper.scrape(category_url, limit=1)
    # print(tournaments)

    # url = "https://www.flashscore.co.uk/tennis/atp-singles/australian-open/results/"
    url = "https://www.flashscore.co.uk/tennis/atp-singles/madrid/results/"
    # url = "https://www.flashscore.co.uk/tennis/atp-singles/halle/results/"

    matches = await scraper.scrape(url)
    print(matches)


if __name__ == "__main__":
    asyncio.run(test())
