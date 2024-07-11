import re
import sys
from pathlib import Path
from abc import ABC, abstractmethod
from aiohttp.client_exceptions import ClientOSError, ServerDisconnectedError


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(ROOT_DIR))

from settings import settings
from service.base_scraper import BaseScraper
from manager.service import SportType, SPORT, StatusCode
from model.service import TournamentNameParsed


FS_MAX_RATE = settings.FLASHSCORE_MAX_RATE
FS_RATE_PERIOD = settings.FLASHSCORE_RATE_PERIOD


class TournamentNameParser:
    @classmethod
    def parse(
        cls,
        tournament_fullname: str,
    ) -> TournamentNameParsed:
        fullspl = tournament_fullname.split(":")
        if len(fullspl) >= 2:
            tournament_category = fullspl[0].strip()

            rightspl = ":".join(fullspl[1:])
            partspl = rightspl.split("-")
            if len(partspl) == 1:
                tournament_name = partspl[0].strip()
                tournament_stage = None
            elif len(partspl) == 2:
                tournament_name = partspl[0].strip()
                tournament_stage = partspl[1].strip()
            elif len(partspl) > 2:
                if "final" in partspl[-1]:
                    tournament_stage = "-".join(partspl[-2:]).strip()
                else:
                    tournament_stage = partspl[-1].strip()
                tournament_name = "-".join(partspl[:-1]).strip()

        return TournamentNameParsed(
            tournament_fullname=tournament_fullname,
            tournament_category=tournament_category,
            tournament_name=tournament_name,
            tournament_stage=tournament_stage,
        )


class FlashScoreScraper(BaseScraper, ABC):
    def __init__(self, proxy: str = None, debug: bool = False):
        super().__init__(
            proxy=proxy,
            max_rate=FS_MAX_RATE,
            rate_period=FS_RATE_PERIOD,
            debug=debug,
        )

    @property
    def custom_headers(self) -> dict:
        return {
            "accept": "application/json",
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

    async def request(self, url: str) -> str | None:
        try:
            return await super().request(url)
        except ServerDisconnectedError as ex:
            print(ex)
        except ClientOSError as ex:
            print(ex)
        return None

    @abstractmethod
    async def scrape(self):
        pass
