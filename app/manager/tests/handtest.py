import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from manager.service import SPORT, StatusCode
from manager.base import MatchCodesFilter, TournamentFilter, PlayerFilter
from manager.tennis_men import TennisMenManager

## dependencies
from data.tennis_men import TennisMenData
from db.api.tennis_men import TennisMenRepository
from service.flashscore.scraper.match import MatchScraper
from service.flashscore.scraper.tournament import TournamentScraper
from service.flashscore.scraper.tournament import TournamentMatchesScraper
from service.flashscore.scraper.player import PlayerScraper
from service.flashscore.scraper.player import PlayerMatchesScaper
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
        tournament=TournamentScraper(sport=sport),
        tournament_matches=TournamentMatchesScraper(sport=sport),
        player=PlayerScraper(sport=sport),
        player_matches=PlayerMatchesScaper(sport=sport),
    )


async def add_match_test():
    manager = get_manager()
    code = "K831uSar"

    match = await manager.add_match(code=code)
    print(match)


async def add_matches_test():
    manager = get_manager()
    codes = [
        "WGndc4yp",
        "nBkA68Ec",
        "4MfHpTtH",
        "YTzs40z9",
        "Q9bfL1fc",
        "K831uSar",
    ]

    matches = await manager.add_matches(codes=codes)
    print(len(matches))


async def collect_current_matches_test():
    manager = get_manager()
    filter = MatchCodesFilter(
        allowed_categories={"ATP - SINGLES"},
        allowed_statuses=StatusCode.future_set,
    )
    current_matches = await manager.collect_current_matches(filter)
    print(len(current_matches))


async def update_matches_for_week_test():
    manager = get_manager()
    filter = MatchCodesFilter(
        allowed_categories={"ATP - SINGLES"},
        allowed_statuses=StatusCode.finished_set,
    )

    week_matches = await manager.update_matches_for_week(filter)
    print(len(week_matches))


async def collect_tournaments_matches_test():
    manager = get_manager()

    category_urls = ["https://www.flashscore.co.uk/x/req/m_2_5724"]

    tfilter = TournamentFilter(2020, 2022)
    await manager.collect_tournaments_matches(
        category_urls,
        limit=2,
        tournament_filter=tfilter,
    )


async def collect_players_matches_test():
    manager = get_manager()

    rank_urls = [
        "https://d.flashscore.co.uk/x/feed/ran_dSJr14Y8_1",
        "https://d.flashscore.co.uk/x/feed/ran_dSJr14Y8_2",
    ]

    filter = PlayerFilter(min_rank=1, max_rank=10)
    matches = await manager.collect_players_matches(
        rank_urls,
        page_limit=1,
        player_filter=filter,
    )


async def recollect_current_matches_test():
    manager = get_manager()

    not_finished = await manager.recollect_current_matches()
    print(len(not_finished))


if __name__ == "__main__":
    # asyncio.run(collect_current_matches_test())
    asyncio.run(recollect_current_matches_test())

    # asyncio.run(collect_tournaments_matches_test())
    # asyncio.run(collect_players_matches_test())

    # asyncio.run(update_matches_for_week_test())
