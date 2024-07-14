import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query

sys.path.append(str(Path(__file__).parent.parent))

from web.base import BaseRouter
from manager.tennis_men import TennisMenManager
from manager.service import SPORT
from data.tennis_men import TennisMenData
from ml.tennis_men.random import RandomTennisMenPredictor
from ml.tennis_men.standard import StandardTennisMenMLPredictor
from db.api.tennis_men import TennisMenRepository

from service.flashscore.scraper.match import MatchScraper
from service.flashscore.scraper.player import PlayerScraper, PlayerMatchesScaper
from service.flashscore.scraper.week import WeeklyMatchesScraper
from service.betexplorer.scraper import BetExplorerScraper
from service.flashscore.scraper.tournament import (
    TournamentScraper,
    TournamentMatchesScraper,
)


class TennisMenRouter(BaseRouter):
    pass


db = TennisMenRepository()
data = TennisMenData(db)
sport = SPORT.TENNIS_MEN

manager = TennisMenManager(
    sport=sport,
    data=data,
    match=MatchScraper(sport),
    week=WeeklyMatchesScraper(sport),
    odds=BetExplorerScraper(sport),
    tournament=TournamentScraper(sport),
    tournament_matches=TournamentMatchesScraper(sport),
    player=PlayerScraper(sport),
    player_matches=PlayerMatchesScaper(sport),
    predictor=StandardTennisMenMLPredictor(data),
)


router = APIRouter()

TennisMenRouter(router, manager)
