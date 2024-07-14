import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

sys.path.append(str(Path(__file__).parent.parent))

from web.base import BaseRouter
from manager.tennis_women import TennisWomenManager
from manager.service import SPORT
from data.tennis_women import TennisWomenData
from ml.tennis_women.random import RandomTennisWomenPredictor
from ml.tennis_women.standard import StandardTennisWomenMLPredictor
from db.api.tennis_women import TennisWomenRepository

from service.flashscore.scraper.match import MatchScraper
from service.flashscore.scraper.player import PlayerScraper, PlayerMatchesScaper
from service.flashscore.scraper.week import WeeklyMatchesScraper
from service.betexplorer.scraper import BetExplorerScraper
from service.flashscore.scraper.tournament import (
    TournamentScraper,
    TournamentMatchesScraper,
)


class TennisWomenRouter(BaseRouter):
    pass


db = TennisWomenRepository()
data = TennisWomenData(db)
sport = SPORT.TENNIS_WOMEN

manager = TennisWomenManager(
    sport=sport,
    data=data,
    match=MatchScraper(sport),
    week=WeeklyMatchesScraper(sport),
    odds=BetExplorerScraper(sport),
    tournament=TournamentScraper(sport),
    tournament_matches=TournamentMatchesScraper(sport),
    player=PlayerScraper(sport),
    player_matches=PlayerMatchesScaper(sport),
    predictor=StandardTennisWomenMLPredictor(data),
)


router = APIRouter()

TennisWomenRouter(router, manager)
