import sys
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from tqdm.asyncio import tqdm_asyncio

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from model.domain import MatchStatusDTO
from model.prediction import MatchPredictionHA, MatchPrediction1x2
from model.service import (
    MatchSDM,
    MatchCodeSDM,
    TournamentSDM,
    TournamentByYearUrlSDM,
    PlayerSDM,
)
from manager.service import (
    SportType,
    FlashScoreMatchScraperInterface,
    BetExplorerScraperInterface,
    FlashScoreTournamentScraperInterface,
    FlashScoreTournamentMatchesScraperIntefrace,
    FlashScoreWeeklyMatchesScraper,
    FlashScorePlayerScraperInterface,
    FlashScorePlayerMatchesScraperInterface,
    FUTURE_DAYS,
    LAST_WEEK_DAYS,
    StatusCode,
)


class BaseDataInterface(ABC):
    ### MATCH collection methods
    @abstractmethod
    async def find_code(self, code: str) -> MatchStatusDTO:
        pass

    @abstractmethod
    async def find_codes(self, codes: list[str]) -> list[MatchStatusDTO]:
        pass

    @abstractmethod
    async def add_match(self, match: MatchSDM) -> None:
        pass

    @abstractmethod
    async def add_matches(self, matches: list[MatchSDM]) -> None:
        pass

    @abstractmethod
    async def get_match(self, code: str) -> MatchSDM | None:
        pass

    @abstractmethod
    async def get_matches(self, codes: list[str]) -> list[MatchSDM] | None:
        pass

    @abstractmethod
    async def get_filtered_matches(
        self,
        match_filter: "MatchFilter",
        limit: int | None = None,
        skip: int | None = None,
    ) -> list[MatchSDM] | None:
        pass

    ### CURRENT MATCH collection methods
    @abstractmethod
    async def upsert_current_match(self, match: MatchSDM) -> None:
        pass

    @abstractmethod
    async def upsert_current_matches(self, matches: list[MatchSDM]) -> None:
        pass

    @abstractmethod
    async def get_current_match(self, code: str) -> MatchSDM | None:
        pass

    @abstractmethod
    async def get_current_matches(self, codes: list[str]) -> list[MatchSDM] | None:
        pass

    @abstractmethod
    async def get_all_current_matches(self) -> list[MatchSDM] | None:
        pass

    @abstractmethod
    async def get_current_codes(self) -> list[MatchStatusDTO] | None:
        pass

    @abstractmethod
    async def delete_current_match(self, code: str) -> None:
        pass

    @abstractmethod
    async def delete_current_matches(self, codes: list[str]) -> None:
        pass


class BasePredictorInterface(ABC):
    @abstractmethod
    async def predict(
        self,
        code: str,
    ) -> MatchPredictionHA | MatchPrediction1x2:
        pass


class MatchFilter:
    def __init__(
        self,
        error: bool | None = None,
        odds_error: str | None = None,
        statuses: list[str] | set[str] | None = None,
        min_date: int | None = None,
        max_date: int | None = None,
        tournament_categories: list[str] | set[str] | None = None,
        team_codes: list[str] | None = None,
    ) -> None:
        self.error = error
        self.odds_error = odds_error
        self.min_date = min_date
        self.max_date = max_date

        self.statuses = self.setup(statuses)
        self.tournament_categories = self.setup(tournament_categories)
        self.team_codes = self.setup(team_codes)

    def setup(self, iterable):
        if iterable is None:
            return iterable
        elif isinstance(iterable, set):
            return iterable
        return set(iterable)

    def dump(self) -> dict:
        filters = {}
        if self.error is not None:
            filters.update({"error": self.error})
        if self.statuses is not None:
            filters.update({"status": {"$in": list(self.statuses)}})
        if self.odds_error is not None:
            filters.update({"odds.error": self.odds_error})
        if self.min_date is not None:
            filters.update({"description.start_date": {"$gte": self.min_date}})
        if self.max_date is not None:
            filters.update({"description.start_date": {"$lte": self.max_date}})
        if self.tournament_categories is not None:
            filters.update(
                {"tournament_category": {"$in": list(self.tournament_categories)}}
            )
        if self.team_codes is not None:
            filters.update(
                {
                    "$or": [
                        {"description.code_t1": {"$in": list(self.team_codes)}},
                        {"description.code_t2": {"$in": list(self.team_codes)}},
                    ]
                }
            )
        return filters

    def filter(self, matches: list[MatchSDM]) -> list[MatchSDM]:
        # return matches
        raise NotImplementedError


class MatchCodesFilter:
    def __init__(
        self,
        min_date: int | None = None,
        max_date: int | None = None,
        allowed_categories: set[str] | list[str] = [],
        disallowed_categories: set[str] | list[str] = [],
        allowed_statuses: set[str] | list[str] = [],
        disallowed_statuses: set[str] | list[str] = [],
    ) -> None:
        self.min_date = min_date
        self.max_date = max_date
        self.allowed_categories = self.setup(allowed_categories)
        self.disallowed_categories = self.setup(disallowed_categories)
        self.allowed_statuses = self.setup(allowed_statuses)
        self.disallowed_statuses = self.setup(disallowed_statuses)

    def setup(self, iterable):
        if isinstance(iterable, set):
            return iterable
        return set(iterable)

    def _filter(self, match: MatchCodeSDM) -> bool:
        if self.min_date and match.date < self.min_date:
            return False
        if self.max_date and match.date > self.max_date:
            return False
        if (
            self.allowed_categories
            and match.tournament_category not in self.allowed_categories
        ):
            return False
        if (
            self.disallowed_categories
            and match.tournament_category in self.disallowed_categories
        ):
            return False
        if self.allowed_statuses and match.status not in self.allowed_statuses:
            return False
        if self.disallowed_statuses and match.status in self.disallowed_statuses:
            return False

        return True

    def filter(
        self,
        match_codes: list[MatchCodeSDM],
    ) -> list[MatchCodeSDM]:
        codemap: dict[str, MatchCodeSDM] = dict()
        for match_code in match_codes:
            if match_code.code in codemap:
                continue

            if self._filter(match_code):
                codemap[match_code.code] = match_code

        return codemap.values()


class PlayerFilter:
    def __init__(
        self,
        min_rank: int | None = None,
        max_rank: int | None = None,
    ) -> None:
        self.min_rank = min_rank
        self.max_rank = max_rank

    def filter(self, players: list[PlayerSDM]) -> list[PlayerSDM]:
        if self.max_rank:
            players = [p for p in players if p.rank <= self.max_rank]
        if self.min_rank:
            players = [p for p in players if p.rank >= self.min_rank]
        return players


class TournamentFilter:
    def __init__(
        self,
        tournament_min_year: int | None = None,
        tournament_max_year: int | None = None,
        allowed_tournaments_categories: set[str] = set(),
    ) -> None:
        self.tournament_min_year = tournament_min_year
        self.tournament_max_year = tournament_max_year
        self.allowed_tournaments_categories = self.setup(allowed_tournaments_categories)

    def setup(self, iterable):
        if isinstance(iterable, set):
            return iterable
        return set(iterable)

    def by_year_filter(
        self,
        by_year: list[TournamentByYearUrlSDM],
    ) -> list[TournamentByYearUrlSDM]:
        if self.tournament_min_year:
            by_year = [
                by for by in by_year if by.start_year >= self.tournament_min_year
            ]
        if self.tournament_max_year:
            by_year = [
                by for by in by_year if by.start_year <= self.tournament_max_year
            ]
        return by_year

    def tournament_filter(
        self,
        tournaments: list[TournamentSDM],
    ) -> list[TournamentSDM]:
        if self.allowed_tournaments_categories:
            return [
                t
                for t in tournaments
                if t.category in self.allowed_tournaments_categories
            ]
        return tournaments


class AbstractManager(ABC):
    @abstractmethod
    async def find_code(self, code: str) -> MatchStatusDTO | None:
        pass

    @abstractmethod
    async def find_codes(self, codes: list[str]) -> list[MatchStatusDTO]:
        pass

    @abstractmethod
    async def add_match(self, code: str) -> MatchSDM | None:
        pass

    @abstractmethod
    async def add_matches(self, codes: list[str]) -> list[MatchSDM] | None:
        pass


class BaseManager(AbstractManager):
    def __init__(
        self,
        sport: SportType,
        data: BaseDataInterface,
        match: FlashScoreMatchScraperInterface,
        week: FlashScoreWeeklyMatchesScraper,
        odds: BetExplorerScraperInterface,
        predictor: BasePredictorInterface,
    ) -> None:
        self.sport = sport
        self.data = data

        self.match = match
        self.week = week
        self.odds = odds

        self.predictor = predictor

    async def scrape_match_data(self, code: str) -> MatchSDM:
        ### Potenial optimization
        # tasks = [
        #     asyncio.create_task(self.match.scrape(code)),
        #     asyncio.create_task(self.odds.scrape(code)),
        # ]
        # match_data, odds_data = await asyncio.gather(*tasks)

        try:
            match_data = None
            match_data = await self.match.scrape(code)
            odds_data = await self.odds.scrape(code)

            match_data.odds = odds_data
            if match_data.status is None:
                match_data.status = StatusCode.UNDEFINED

            return match_data

        except Exception as ex:
            print("Exception at code", code, ex)
            if match_data is None:
                match_data = MatchSDM(
                    code=code,
                    error=True,
                    status=StatusCode.UNDEFINED,
                )
            if match_data.status is None:
                match_data.status = StatusCode.UNDEFINED

            return match_data

    async def find_code(self, code: str) -> MatchStatusDTO | None:
        """Return match code and status if exists in the database"""
        return await self.data.find_code(code)

    async def find_codes(self, codes: list[str]) -> list[MatchStatusDTO]:
        """Return match codes and statuses if codes exists in the database"""
        return await self.data.find_codes(codes)

    async def get_match(self, code: str) -> MatchSDM | None:
        return await self.data.get_match(code)

    async def get_all_current_matches(self) -> list[MatchSDM] | None:
        return await self.data.get_all_current_matches()

    async def get_prediction(self, code: str) -> MatchPredictionHA | MatchPrediction1x2:
        return await self.predictor.predict(code)

    async def add_match(self, code: str) -> MatchSDM | None:
        found = await self.find_code(code)
        if found:
            return None

        match_data = await self.scrape_match_data(code)
        await self.data.add_match(match_data)
        return match_data

    async def add_matches(self, codes: list[str]) -> list[MatchSDM] | None:
        founded_codes = await self.find_codes(codes)
        founded_codes = {c.code for c in founded_codes}
        codes = [c for c in codes if c not in founded_codes]
        if not codes:
            return None

        tasks = [asyncio.create_task(self.scrape_match_data(c)) for c in codes]
        print("Scrape matches:", len(codes))
        matches_data = await tqdm_asyncio.gather(*tasks)

        await self.data.add_matches(matches_data)
        return matches_data

    async def collect_current_matches(
        self,
        codes_filter: MatchCodesFilter | None,
    ) -> list[MatchSDM]:
        """
        Collect current matches and add them to 'current' collection.
        Current: live + future matches.
        """

        allowed_statuses = StatusCode.future_set
        allowed_statuses = allowed_statuses.union(StatusCode.live_set)
        if not codes_filter:
            codes_filter = MatchCodesFilter()
        codes_filter.allowed_statuses = allowed_statuses

        codes = await self.week.scrape(FUTURE_DAYS)
        codes = codes_filter.filter(codes) if codes_filter else codes

        tasks = [asyncio.create_task(self.scrape_match_data(mc.code)) for mc in codes]
        matches = await asyncio.gather(*tasks)

        await self.data.upsert_current_matches(matches)
        return matches

    async def recollect_current_matches(self) -> list[MatchSDM]:
        current = await self.data.get_current_codes()

        tasks = [asyncio.create_task(self.scrape_match_data(mc.code)) for mc in current]
        recollected = await asyncio.gather(*tasks)

        finished: list[MatchSDM] = []
        not_finished: list[MatchSDM] = []
        for match in recollected:
            if StatusCode.finished(match.status):
                finished.append(match)
            else:
                not_finished.append(match)

        ### update not finished matches
        await self.data.upsert_current_matches(not_finished)

        ### delete finished matches from current
        await self.data.delete_current_matches([m.code for m in finished])

        ### add finished matches in matches
        await self.data.add_matches(finished)

        return not_finished

    async def update_matches_for_week(
        self,
        codes_filter: MatchCodesFilter | None,
    ) -> list[MatchSDM]:
        """
        Collect matches for the last week and add them to matches collection.
        Recommended to filter matches with StatusCode.finished_set.
        """

        allowed_statuses = StatusCode.finished_set
        if not codes_filter:
            codes_filter = MatchCodesFilter()
        codes_filter.allowed_statuses = allowed_statuses

        codes = await self.week.scrape(LAST_WEEK_DAYS)
        codes = codes_filter.filter(codes) if codes_filter else codes
        matches = await self.add_matches([mc.code for mc in codes])

        return matches

    @abstractmethod
    async def update_matches_for_year(self) -> list[MatchSDM]:
        pass


class TournamentsManagerMixin(AbstractManager):
    def __init__(
        self,
        tournament: FlashScoreTournamentScraperInterface,
        tournament_matches: FlashScoreTournamentMatchesScraperIntefrace,
    ) -> None:
        self.tournament = tournament
        self.tournament_matches = tournament_matches

    async def scrape_tournaments(
        self,
        category_urls: list[str],
        limit: int | None = None,
        tournament_filter: TournamentFilter | None = None,
    ) -> list[TournamentSDM]:
        tasks = [
            asyncio.create_task(self.tournament.scrape(url, limit))
            for url in category_urls
        ]
        tournaments = await asyncio.gather(*tasks)
        tournaments = [t for sub in tournaments for t in sub]

        if tournament_filter:
            tournaments = tournament_filter.tournament_filter(tournaments)

        return tournaments

    async def scrape_tournaments_by_year(
        self,
        tournaments: list[TournamentSDM],
        tournament_filter: TournamentFilter | None,
        codes_filter: MatchCodesFilter | None = None,
    ) -> list[MatchCodeSDM]:
        by_year = [by for t in tournaments for by in t.by_year_urls]
        if tournament_filter:
            by_year = tournament_filter.by_year_filter(by_year)

        tasks = [
            asyncio.create_task(self.tournament_matches.scrape(by.url))
            for by in by_year
        ]

        codes = await asyncio.gather(*tasks)
        codes = [c for sub in codes for c in sub]
        if codes_filter:
            codes = codes_filter.filter()

        return codes

    async def collect_tournaments_matches(
        self,
        category_urls: list[str],
        limit: int | None = None,
        tournament_filter: TournamentFilter | None = None,
        codes_filter: MatchCodesFilter | None = None,
    ):
        """
        Here we don't need prepared codes_filter to check match on finished feature.
        It's because we scrape tournament results - matches finished by default.
        """

        tournaments = await self.scrape_tournaments(
            category_urls,
            limit,
            tournament_filter,
        )

        codes = await self.scrape_tournaments_by_year(
            tournaments,
            tournament_filter,
            codes_filter,
        )

        matches = await self.add_matches([c.code for c in codes])
        return matches


class PlayersManagerMixin(AbstractManager):
    def __init__(
        self,
        player: FlashScorePlayerScraperInterface,
        player_matches: FlashScorePlayerMatchesScraperInterface,
    ) -> None:
        self.player = player
        self.player_matches = player_matches

    async def scrape_players(
        self,
        rank_urls: list[str],
        player_filter: PlayerFilter | None = None,
    ) -> list[PlayerSDM]:
        tasks = [asyncio.create_task(self.player.scrape(url)) for url in rank_urls]
        players = await asyncio.gather(*tasks)
        players = [p for sub in players for p in sub]
        if player_filter:
            players = player_filter.filter(players)
        return players

    async def scrape_players_match_codes(
        self,
        players: list[PlayerSDM],
        page_limit: int,
        codes_filter: MatchCodesFilter | None = None,
    ) -> list[MatchCodeSDM]:
        tasks = [
            asyncio.create_task(self.player_matches.scrape(p, page_limit))
            for p in players
        ]

        print("Scrape match codes from players:", len(players))
        codes = await tqdm_asyncio.gather(*tasks)
        codes = [c for sub in codes for c in sub]
        codes = codes_filter.filter(codes)
        return codes

    async def collect_players_matches(
        self,
        rank_urls: list[str],
        page_limit: int = 20,
        player_filter: PlayerFilter | None = None,
        codes_filter: MatchCodesFilter | None = None,
    ) -> list[MatchSDM]:
        """
        Here we need prepared codes_filter to get rid of dups along players codes.
        But we don't need to check match status on finished feature.
        It's because we scrape player results - matches finished by default.
        """

        ### we use MatchCodesFilter to get rid of dups along players codes
        if not codes_filter:
            codes_filter = MatchCodesFilter()

        players = await self.scrape_players(rank_urls, player_filter)
        codes = await self.scrape_players_match_codes(players, page_limit, codes_filter)

        matches = await self.add_matches([mc.code for mc in codes])
        return matches
