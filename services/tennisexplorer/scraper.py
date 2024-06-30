import re
import sys
import asyncio
from abc import ABC, abstractmethod
from pprint import pprint
from pathlib import Path
from bs4 import BeautifulSoup as soup
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from services.base_scraper import BaseScraper, SportType, SPORT
from models import Rank, TennisPlayerData

TE_MAX_RATE = 20
TE_RATE_PERIOD = 1

MAX_PAGE = 40


class TennisExplorerSraper(BaseScraper, ABC):
    def __init__(
        self,
        proxy: str = None,
        max_rate: int = TE_MAX_RATE,
        rate_period: float = TE_RATE_PERIOD,
        debug: bool = False,
        sport: SportType = SPORT.TENNIS_MEN,
    ) -> None:
        super().__init__(proxy, max_rate, rate_period, debug)

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
            "x-fsign": "SW9D1eZo",
            "sec-ch-ua-platform": '"Linux"',
        }

    @abstractmethod
    async def scrape(self):
        pass


class TennisExplorerRankDatesScraper(TennisExplorerSraper):
    def parse(self, response: str) -> list[str]:
        s = soup(response, "lxml")

        dates = []
        raw_dates = s.find("select", {"name": "date"}).find_all("option")
        for i in raw_dates:
            date = i.get("value")
            dates.append(date)

        return dates

    async def scrape(self, min_y: int, max_y: int) -> list[str]:
        if self.sport.tennis_explorer is None:
            raise ValueError("SportType doesn't have tennis_explorer url")

        years = list(range(min_y, max_y))
        urls = [self.sport.tennis_explorer + f"{y}" for y in years]

        tasks = [self.request(url) for url in urls]
        responses = await asyncio.gather(*tasks)

        dates = [self.parse(r) for r in responses]
        dates = [d for sub in dates for d in sub]

        return dates


class TennisExplorerRankScraper(TennisExplorerSraper):
    def get_urls(self, dates: list[str]):
        urls: list[str] = []
        for date in dates:
            for page_index in range(1, MAX_PAGE + 1):
                url = self.sport.tennis_explorer + f"?date={date}&page={page_index}"
                urls.append(url)

        return urls

    def parse_page(self, response: str) -> list[Rank]:
        s = soup(response, "lxml")
        rows = s.find("tbody", {"class": "flags"}).find_all(
            "tr", {"onmouseover": "m_over(this);"}
        )

        date = (
            s.find(
                "select",
                {
                    "name": "date",
                    "id": "rform-date",
                },
            )
            .find("option", {"selected": "selected"})
            .get("value")
        )

        ranks: list[Rank] = []

        date = int(datetime.strptime(date, "%Y-%m-%d").timestamp())
        for index in range(len(rows)):
            row = rows[index]

            rank = row.find("td", {"class": "rank first"}).text.split(".")[0]
            points = row.find("td", {"class": "long-point"}).text
            name = row.find("td", {"class": "t-name"}).text
            te_id = row.find("td", {"class": "t-name"}).a.get("href")

            rank = Rank(date=date, rank=rank, points=points, name=name, te_id=te_id)
            ranks.append(rank)

        return ranks

    async def scrape_page(self, url: str) -> list[Rank]:
        response = await self.request(url)
        ranks = self.parse_page(response)
        return ranks

    async def scrape(self, dates: list[str]) -> list[Rank]:
        urls = self.get_urls(dates)

        tasks = [asyncio.create_task(self.scrape_page(url)) for url in urls]
        ranks = await asyncio.gather(*tasks)
        ranks = [r for sub in ranks for r in sub]

        return ranks


class TennisExplorerPlayerScraper(TennisExplorerSraper):
    def parse(self, response: str, te_id: str) -> TennisPlayerData:
        s = soup(response, "lxml")
        box = s.find("div", {"id": "center"}).find(
            "div", {"class": "box boxBasic lGray"}
        )

        name = box.find("h3").text
        country = None
        height = None
        weight = None
        birthday = None
        plays = None
        career_start = None

        rows = box.find_all("div", {"class": "date"})
        for row in rows:
            if "Country" in row.text:
                country = row.text.split(":")[1].strip()
            elif "Height / Weight" in row.text:
                height = row.text.split(":")[1].split("/")[0].split("cm")[0].strip()
                weight = row.text.split(":")[1].split("/")[1].split("kg")[0].strip()
            elif "Age" in row.text:
                birthday = row.text.split(":")[1].split("(")[1].split(")")[0]
                birthday = int(datetime.strptime(birthday, "%d. %m. %Y").timestamp())
            elif "Plays" in row.text:
                plays = row.text.split(":")[1].strip()

        box = s.find("div", {"id": "center"}).find_all("div", {"class": "box lGray"})[2]
        years = box.find("table", {"class": "result balance"}).find_all(
            "td", {"class": "year"}
        )
        if len(years) > 0:
            career_start = years[-1].a.text

        return TennisPlayerData(
            te_id=te_id,
            name=name,
            country=country,
            height=height,
            weight=weight,
            birthday=birthday,
            plays=plays,
            career_start=career_start,
        )

    async def scrape(self, tennis_explorer_id: str):
        url = "https://www.tennisexplorer.com" + tennis_explorer_id

        response = await self.request(url)
        player = self.parse(response, tennis_explorer_id)
        print(player)


async def test():
    dates_scraper = TennisExplorerRankDatesScraper(sport=SPORT.TENNIS_MEN)
    rank_scraper = TennisExplorerRankScraper(sport=SPORT.TENNIS_MEN)
    player_scraper = TennisExplorerPlayerScraper(sport=SPORT.TENNIS_MEN)

    dates = await dates_scraper.scrape(2022, 2025)
    ranks = await rank_scraper.scrape(dates[:2])

    te_id = "/player/alcaraz-5ab70/"
    data = await player_scraper.scrape(te_id)


if __name__ == "__main__":
    asyncio.run(test())
