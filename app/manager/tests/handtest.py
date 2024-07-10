import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from manager.service import SPORT
from manager.tennis_men import TennisMenManager

## dependencies
from data.tennis_men import TennisMenData
from db.api.tennis_men import TennisMenRepository
from service.flashscore.scraper.match import MatchScraper
from service.flashscore.scraper.tournament import TournamentScraper
from service.flashscore.scraper.tournament import TournamentMatchesScraper
from service.flashscore.scraper.week import WeeklyMatchesScraper
from service.betexplorer.scraper import BetExplorerScraper


def get_manager() -> TennisMenManager:
    sport = SPORT.TENNIS_MEN
    return TennisMenManager(
        sport=sport,
        data=TennisMenData(TennisMenRepository()),
        match=MatchScraper(sport=sport),
        week=WeeklyMatchesScraper(sport=sport),
        odds=BetExplorerScraper(sport=sport),
    )


async def add_match_test():
    manager = get_manager()
    code = "K831uSar"

    match = await manager.add_match(code=code)
    print(match)


async def collect_future_matches_test():
    manager = get_manager()
    future_matches = await manager.collect_future_matches()
    print(future_matches)


if __name__ == "__main__":
    asyncio.run(collect_future_matches_test())
