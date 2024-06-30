import re
import sys
import asyncio
from pprint import pprint
from pathlib import Path
from bs4 import BeautifulSoup as soup
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from services.base_scraper import BaseScraper, SportType, SPORT
from models import MatchOdds1x2, MatchOddsHA, BookOddsHA, BookOdds1x2, OddsType

BE_MAX_RATE = 20
BE_RATE_PERIOD = 1

ODDS_CHECK = "Unfortunately there wasn't any bookmaker offering odds for this match"
ODDS_BUG = "A match with the given ID doesn't exist"


class BetExplorerParser:
    def parse_ha(self, response: str, match: MatchOddsHA) -> MatchOddsHA:
        bookmakers = response.split("<tr data-bid=")[1:]

        for book in bookmakers:
            name = re.search(r"'event-name'\: '(.*?)',", book).group(1)

            odds = re.findall(r'data-odd=\\"(.*?)\\"', book)
            odds = odds[:2] if odds else odds
            odds_date = re.search(r'data-created=\\"(.*?)\\"', book).group(1)
            odds_date = datetime.strptime(odds_date, "%d,%m,%Y,%H,%M")
            odds_date = int(odds_date.timestamp()) - 3600  # transform to gmt-0

            open_odds = re.findall(r'data-opening-odd=\\"(.*?)\\"', book)
            if open_odds:
                oped_odds_date = re.search(
                    r'data-opening-date=\\"(.*?)\\"', book
                ).group(1)
                oped_odds_date = datetime.strptime(oped_odds_date, "%d,%m,%Y,%H,%M")
                oped_odds_date = (
                    int(oped_odds_date.timestamp()) - 3600
                )  # transform to gmt-0
            else:
                open_odds = [None, None]
                oped_odds_date = None

            book_odds = BookOddsHA(
                name=name,
                odds_t1=odds[0],
                odds_t2=odds[1],
                odds_date=odds_date,
                open_odds_t1=open_odds[0],
                open_odds_t2=open_odds[1],
                open_odds_date=oped_odds_date,
            )
            match.odds.append(book_odds)

        return match

    def parse_1x2(self, response: str, match: MatchOdds1x2) -> MatchOdds1x2:
        book_raw = response.split("<tr  class")[1:-1]
        book_raw = [b.split(r"<\/span><\/td>\n<\/tr>") for b in book_raw]

        bookmakers = []
        for book in book_raw:
            if len(book) == 2:
                bookmakers.append(book[0])
            else:
                bookmakers.append(book[0])
                bookmakers.append(book[1])
                bookmakers.append(book[2])

        bookmakers = [b for b in bookmakers if len(b) > 20]

        for book in bookmakers:
            name = re.search(r"'event-name'\: '(.*?)',", book).group(1)

            odds = re.findall(r'data-odd=\\"(.*?)\\"', book)
            odds_date = re.search(r'data-created=\\"(.*?)\\"', book).group(1)
            odds_date = datetime.strptime(odds_date, "%d,%m,%Y,%H,%M")
            odds_date = int(odds_date.timestamp()) - 3600  # transform to gmt-0

            open_odds = re.findall(r'data-opening-odd=\\"(.*?)\\"', book)
            if len(open_odds) > 0:
                oped_odds_date = re.search(
                    r'data-opening-date=\\"(.*?)\\"', book
                ).group(1)
                oped_odds_date = datetime.strptime(oped_odds_date, "%d,%m,%Y,%H,%M")
                oped_odds_date = (
                    int(oped_odds_date.timestamp()) - 3600
                )  # transform to gmt-0
            else:
                open_odds = [None, None, None]
                oped_odds_date = None

            book_odds = BookOdds1x2(
                name=name,
                odds_t1=odds[0],
                odds_x=odds[1],
                odds_t2=odds[2],
                odds_date=odds_date,
                open_odds_t1=open_odds[0],
                open_odds_x=open_odds[1],
                open_odds_t2=open_odds[2],
                open_odds_date=oped_odds_date,
            )
            match.odds.append(book_odds)

        return match


class BetExplorerScraper(BaseScraper):
    """Scrape players from rank"""

    def __init__(
        self,
        proxy: str = None,
        max_rate: int = BE_MAX_RATE,
        rate_period: float = BE_RATE_PERIOD,
        debug: bool = False,
        sport: SportType = SPORT.TENNIS_MEN,
    ) -> None:
        super().__init__(proxy, max_rate, rate_period, debug)

        self.parser = BetExplorerParser()
        self.sport = sport

    @property
    def custom_headers(self) -> dict:
        return {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "referer": "https://d.flashscore.ru.com/x/feed/proxy-fetch",
            "sec-ch-ua": '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "x-fsign": "SW9D1eZo",
            "sec-ch-ua-platform": '"Linux"',
        }

    def is_bug(self, response: str) -> bool:
        if ODDS_BUG in response:
            return True
        return False

    def no_odds(self, response: str) -> bool:
        if ODDS_CHECK in response:
            return True
        return False

    def checkout(
        self,
        match: MatchOdds1x2 | MatchOddsHA,
        response: str,
    ) -> MatchOdds1x2 | MatchOddsHA:
        if self.no_odds(response):
            match.is_odds = False
        elif self.is_bug(response):
            match.is_odds = False
            match.error = True
        else:
            match.is_odds = True

        return match

    async def scrape_ha(self, code: str) -> MatchOddsHA:
        url = f"https://www.betexplorer.com/match-odds-old/{code}/1/ha/1/"
        response = await self.request(url)

        match = MatchOddsHA(code=code, odds_type=OddsType.ODDS_HA)
        match = self.checkout(match, response)
        if match.is_odds:
            match = self.parser.parse_ha(response, match)

        return match

    async def scrape_1x2(self, code: str) -> MatchOdds1x2:
        url = f"https://www.betexplorer.com/match-odds/{code}/1/1x2/bestOdds/"
        response = await self.request(url)

        match = MatchOdds1x2(code=code, odds_type=OddsType.ODDS_1x2)
        match = self.checkout(match, response)
        if match.is_odds:
            match = self.parser.parse_1x2(response, match)

        return match

    async def scrape(self, code: str) -> MatchOddsHA | MatchOdds1x2:
        if self.sport.odds_type == OddsType.ODDS_1x2:
            return await self.scrape_1x2(code)
        elif self.sport.odds_type == OddsType.ODDS_HA:
            return await self.scrape_ha(code)
        else:
            raise NotImplementedError(
                f"Scraping of '{self.sport.odds_type}' odds type is not implemented"
            )


async def test_ha():
    scraper = BetExplorerScraper()

    code = "21vkvxmJ"
    data = await scraper.scrape_ha(code)
    print(data)


async def test_ha_empty():
    scraper = BetExplorerScraper()

    code = "Mou7sEg6"
    data = await scraper.scrape_ha(code)
    # print(data)


async def test_1x2():
    scraper = BetExplorerScraper()

    code = "hph7lsj3"
    data = await scraper.scrape_1x2(code)
    print(data)


if __name__ == "__main__":
    asyncio.run(test_ha())
