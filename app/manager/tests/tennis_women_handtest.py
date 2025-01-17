import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from manager.service import SPORT, StatusCode
from manager.base import MatchCodesFilter, TournamentFilter, PlayerFilter
from manager.tennis_women import TennisWomenManager

## dependencies
from data.tennis_women import TennisWomenData
from db.api.tennis_women import TennisWomenRepository
from service.flashscore.scraper.match import MatchScraper
from service.flashscore.scraper.tournament import TournamentScraper
from service.flashscore.scraper.tournament import TournamentMatchesScraper
from service.flashscore.scraper.player import PlayerScraper
from service.flashscore.scraper.player import PlayerMatchesScaper
from service.flashscore.scraper.week import WeeklyMatchesScraper
from service.betexplorer.scraper import BetExplorerScraper
from ml.tennis_women.standard import StandardTennisWomenMLPredictor


def get_manager() -> TennisWomenManager:
    sport = SPORT.TENNIS_WOMEN
    db = TennisWomenRepository()
    data = TennisWomenData(db)
    return TennisWomenManager(
        sport=sport,
        data=data,
        match=MatchScraper(sport=sport),
        week=WeeklyMatchesScraper(sport=sport),
        odds=BetExplorerScraper(sport=sport),
        tournament=TournamentScraper(sport=sport),
        tournament_matches=TournamentMatchesScraper(sport=sport),
        player=PlayerScraper(sport=sport),
        player_matches=PlayerMatchesScaper(sport=sport),
        predictor=StandardTennisWomenMLPredictor(data=data),
    )


async def add_match_test():
    manager = get_manager()
    code = "Yq5BO72S"

    match = await manager.add_match(code=code)
    print(match)


async def add_matches_test():
    manager = get_manager()
    codes = [
        "QcO18Z2n",
        "zPsFNJu1",
        "UVpnRkml",
        "GzLYPSjf",
        "KnvC2bld",
        "Yq5BO72S",
    ]

    matches = await manager.add_matches(codes=codes)
    if matches:
        print(len(matches))
    else:
        print(0)


async def collect_current_matches_test():
    manager = get_manager()
    filter = MatchCodesFilter(
        allowed_categories={"WTA - SINGLES"},
        allowed_statuses=StatusCode.future_set,
    )
    current_matches = await manager.collect_current_matches(filter)
    print(len(current_matches))


async def update_matches_for_week_test():
    manager = get_manager()
    filter = MatchCodesFilter(
        allowed_categories={"WTA - SINGLES"},
        allowed_statuses=StatusCode.finished_set,
    )

    week_matches = await manager.update_matches_for_week(filter)
    print(len(week_matches))


async def collect_tournaments_matches_test():
    manager = get_manager()

    category_urls = ["https://www.flashscore.co.uk/x/req/m_2_5725"]

    tfilter = TournamentFilter(2022, 2024)
    await manager.collect_tournaments_matches(
        category_urls,
        tournament_filter=tfilter,
    )


async def collect_players_matches_test():
    manager = get_manager()

    rank_urls = [
        "https://local-uk.flashscore.ninja/5/x/feed/ran_hfDiar3L_1",
        "https://local-uk.flashscore.ninja/5/x/feed/ran_hfDiar3L_2",
    ]

    pfilter = PlayerFilter(min_rank=1, max_rank=200)
    cfilter = MatchCodesFilter(
        min_date=1640916794,
        allowed_categories={"WTA - SINGLES"},
    )

    await manager.collect_players_matches(
        rank_urls,
        page_limit=5,
        player_filter=pfilter,
        codes_filter=cfilter,
    )


async def recollect_current_matches_test():
    manager = get_manager()

    not_finished = await manager.recollect_current_matches()
    print(len(not_finished))


if __name__ == "__main__":
    # asyncio.run(add_match_test())
    # asyncio.run(add_matches_test())

    # asyncio.run(update_matches_for_week_test())

    # asyncio.run(collect_tournaments_matches_test())
    # asyncio.run(collect_players_matches_test())

    asyncio.run(collect_current_matches_test())
    # asyncio.run(recollect_current_matches_test())
