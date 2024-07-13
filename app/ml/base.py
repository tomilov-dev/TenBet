import os
import sys
import bisect
import pickle
from pathlib import Path

import pandas as pd
from pydantic import BaseModel
from tqdm import tqdm
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from model.prediction import MatchPredictionHA, MatchPrediction1x2
from manager.base import BasePredictorInterface, BaseDataInterface
from manager.service import SportType
from manager.base import MatchFilter
from model.service import MatchSDM


TARGET = "target"

TMP_DAY = 86400
TMP_WEEK = TMP_DAY * 7
TMP_MONTH = TMP_DAY * 30
TMP_YEAR = TMP_DAY * 365

NA_FILLER_FILENAME = "na_filler.xlsx"
PREPROCESSED_FEATURES_FILENAME = "preprocessed_features.xlsx"
MODEL_FILENAME = "model.pkl"


class BasePreditor(BasePredictorInterface):
    def __init__(
        self,
        sport: SportType,
        data: BaseDataInterface,
    ) -> None:
        self.sport = sport
        self.data = data


class ByTeam(BaseModel):
    date: int


class StatsByTeam(ByTeam):
    stats: dict


class MatchByTeam(ByTeam):
    match: MatchSDM


class StatValue(BaseModel):
    value: int | float | list[int | float] | None = None
    count: int


class StandardML:
    DIST_DIR = None

    def __init__(
        self,
        sport: SportType,
        data: BaseDataInterface,
    ) -> None:
        self.sport = sport
        self.data = data

        if self.DIST_DIR is None:
            raise ValueError("You should set DIST DIR")

    def save_model(self, model):
        with open(self.DIST_DIR / MODEL_FILENAME, "wb") as f:
            pickle.dump(model, f)

    def upload_model(self):
        with open(self.DIST_DIR / MODEL_FILENAME, "rb") as f:
            return pickle.load(f)

    def setup_target(self, match: MatchSDM) -> int:
        winner = match.description.winner
        if winner is None:
            return winner

        if winner == 0:
            ### FS winner 0 -> draw (for me it's 2)
            winner = 2
        elif winner == 1:
            ### FS winner 1 -> t1 win (t1 win for me 1)
            winner = 1
        elif winner == 2:
            ### FS winner 2 -> t1 lose (t1 win for me 0)
            winner = 0
        else:
            raise ValueError("Winner < 0 or > 2")

        return winner

    def group_by_team(self, matches: list[MatchSDM]) -> tuple[
        dict[str, list[StatsByTeam]],
        dict[str, list[MatchByTeam]],
        set[str],
    ]:
        def add(mapper: dict[str, list], team: str, value) -> None:
            if team not in mapper:
                mapper[team] = [value]
            else:
                mapper[team].append(value)

        stats_by_teams: dict[str, list[StatsByTeam]] = dict()
        matches_by_teams: dict[str, list[MatchByTeam]] = dict()
        stats_keys: set[str] = set()

        for match in matches:
            start_date = match.description.start_date
            ct1 = match.description.code_t1
            ct2 = match.description.code_t2

            for time in match.statistics1:
                stkeys = set(match.statistics1[time].keys())
                stats_keys.update(stkeys)

            stbt1 = StatsByTeam(date=start_date, stats=match.statistics1)
            mbt1 = MatchByTeam(date=start_date, match=match)
            add(stats_by_teams, ct1, stbt1)
            add(matches_by_teams, ct1, mbt1)

            stbt2 = StatsByTeam(date=start_date, stats=match.statistics2)
            mbt2 = MatchByTeam(date=start_date, match=match)
            add(stats_by_teams, ct2, stbt2)
            add(matches_by_teams, ct2, mbt2)

        return stats_by_teams, matches_by_teams, stats_keys

    def search_stats_by_team(
        self,
        stats_by_teams: dict[str, list[StatsByTeam]],
        code_team: str,
        min_date: int,
        max_date: int,
    ) -> list[dict]:
        stats_by_team = stats_by_teams[code_team]

        start = bisect.bisect_left(stats_by_team, min_date, key=lambda x: x.date)
        end = bisect.bisect_right(stats_by_team, max_date - 1, key=lambda x: x.date)

        return [s.stats for s in stats_by_team[start:end]]

    def search_matches_by_team(
        self,
        matches_by_teams: dict[str, list[MatchByTeam]],
        code_team: str,
        min_date: int,
        max_date: int,
    ) -> list[MatchSDM]:
        matches_by_team = matches_by_teams[code_team]

        start = bisect.bisect_left(matches_by_team, min_date, key=lambda x: x.date)
        end = bisect.bisect_right(matches_by_team, max_date - 1, key=lambda x: x.date)

        return [s.match for s in matches_by_team[start:end]]

    def aggregate_game_stats(
        self,
        stats: list[dict[str, float]],
        time: str,
        stats_keys: set[str],
    ) -> dict[str, StatValue]:
        aggmap: dict[str, StatValue] = {
            k: StatValue(value=None, count=0) for k in stats_keys
        }
        for stat in stats:
            if time not in stat:
                continue

            time_stat: dict = stat[time]
            for stname in time_stat.keys():
                if aggmap[stname].value is None:
                    aggmap[stname] = StatValue(value=time_stat[stname], count=1)
                elif isinstance(aggmap[stname].value, list):
                    aggmap[stname].count += 1
                    aggmap[stname].value[0] += time_stat[stname][0]
                    aggmap[stname].value[1] += time_stat[stname][1]
                else:
                    aggmap[stname].count += 1
                    aggmap[stname].value += time_stat[stname]

        for stname in aggmap:
            stat = aggmap[stname]
            if stat.value is None:
                pass
            elif isinstance(stat.value, list):
                if stat.value[1] == 0:
                    agg = 0
                else:
                    agg = stat.value[0] / stat.value[1]
                stat.value = agg
            else:
                agg = stat.value / stat.count
                stat.value = agg

        return aggmap

    def aggregate_team_stats(
        self,
        matches: list[MatchSDM],
        code_team1: str,
    ) -> dict[str, StatValue]:
        times = ["time1", "time2", "time3", "time4", "time5"]

        aggmap: dict[str, StatValue] = {
            "win_rate": StatValue(value=0, count=0),
            "score_rate": StatValue(value=0, count=0),
            "time_score_rate": StatValue(value=0, count=0),
        }

        for match in matches:
            ct1 = match.description.code_t1
            winner = match.description.winner
            scrt1 = match.description.score_t1
            scrt2 = match.description.score_t2

            if winner is not None:
                tcw = 1 if ct1 == code_team1 else 2
                aggmap["win_rate"].count += 1
                aggmap["win_rate"].value += int(winner == tcw)

            if scrt1 is not None and scrt2 is not None:
                spread = scrt1 - scrt2 if ct1 == code_team1 else scrt2 - scrt1
                aggmap["score_rate"].count += 1
                aggmap["score_rate"].value += spread

            for time in times:
                timescore = getattr(match, time)
                if timescore is None:
                    continue

                scrt1 = timescore.score_t1
                scrt2 = timescore.score_t2
                spread = scrt1 - scrt2 if ct1 == code_team1 else scrt2 - scrt1
                aggmap["time_score_rate"].count += 1
                aggmap["time_score_rate"].value += spread

        for stname in aggmap:
            if aggmap[stname].count == 0:
                aggmap[stname].value = 0
            else:
                aggmap[stname].value = aggmap[stname].value / aggmap[stname].count

        return aggmap

    def h2h_score(
        self,
        matches_by_team1: list[MatchSDM],
        code_team1: str,
        code_team2: str,
    ) -> float:
        wins = 0
        match_count = 0

        for match in matches_by_team1:
            ct1 = match.description.code_t1
            ct2 = match.description.code_t2
            winner = match.description.winner

            if ct1 != code_team2 and ct2 != code_team2:
                continue
            if winner is None:
                continue

            match_count += 1
            t1wc = 1 if ct1 == code_team1 else 2
            wins += int(winner == t1wc)

        h2h = 0.5
        if match_count > 0:
            h2h = wins / match_count
        return h2h

    def setup_match_features(
        self,
        match: MatchSDM,
        time_spread: int,
        stats_by_teams: dict,
        matches_by_teams: dict,
        stats_keys: set[str],
    ):
        def add(
            features: pd.Series,
            stats: dict[str, StatValue],
            postfix: str,
        ) -> None:
            for stname, stval in stats.items():
                features[stname + postfix] = stval.value

        features = pd.Series()

        code_team1 = match.description.code_t1
        code_team2 = match.description.code_t2

        min_date = match.description.start_date - time_spread
        max_date = match.description.start_date - 1

        prev_stats_t1 = self.search_stats_by_team(
            stats_by_teams, code_team1, min_date, max_date
        )
        prev_stats_t2 = self.search_stats_by_team(
            stats_by_teams, code_team2, min_date, max_date
        )

        prev_matches_t1 = self.search_matches_by_team(
            matches_by_teams, code_team1, min_date, max_date
        )
        prev_matches_t2 = self.search_matches_by_team(
            matches_by_teams, code_team2, min_date, max_date
        )

        agg_gamestat_t1 = self.aggregate_game_stats(prev_stats_t1, "match", stats_keys)
        add(features, agg_gamestat_t1, " T1")

        agg_gamestat_t2 = self.aggregate_game_stats(prev_stats_t2, "match", stats_keys)
        add(features, agg_gamestat_t2, " T2")

        agg_teamstat_t1 = self.aggregate_team_stats(prev_matches_t1, code_team1)
        add(features, agg_teamstat_t1, " T1")

        agg_teamstat_t2 = self.aggregate_team_stats(prev_matches_t2, code_team2)
        add(features, agg_teamstat_t2, " T2")

        features["h2h"] = self.h2h_score(prev_matches_t1, code_team1, code_team2)
        features[TARGET] = self.setup_target(match)

        return features


class StandardMLTrainer(StandardML):
    def setup_na_filler(self, train_data: pd.DataFrame) -> pd.Series:
        na_filler = train_data.mean().drop([TARGET], errors="ignore")
        na_filler.to_excel(self.DIST_DIR / NA_FILLER_FILENAME, index=True)
        return na_filler

    def setup_matches_features(
        self,
        matches: list[MatchSDM],
        time_spread: int,
    ) -> pd.DataFrame:
        min_start_date = matches[0].description.start_date + time_spread
        stats_bt, matches_bt, stats_keys = self.group_by_team(matches)

        matches_features: list[pd.Series] = []
        for match in tqdm(matches, desc="Processing matches features"):
            ### time shift to have sufficient amount of statistics
            if match.description.start_date < min_start_date:
                continue

            match_features = self.setup_match_features(
                match,
                time_spread,
                stats_bt,
                matches_bt,
                stats_keys,
            )
            matches_features.append(match_features)

        features_df = pd.DataFrame(matches_features)
        features_df.to_excel(
            self.DIST_DIR / PREPROCESSED_FEATURES_FILENAME, index=False
        )

        return features_df

    async def train(
        self,
        preprocessed_features: bool = False,
        preprocessed_na_filler: bool = False,
    ):
        match_filter = MatchFilter(error=False)
        matches = await self.data.get_filtered_matches(match_filter)

        # matches = matches[:2500]

        if preprocessed_features:
            if not os.path.exists(self.DIST_DIR / PREPROCESSED_FEATURES_FILENAME):
                raise FileExistsError("Preprocessed features file does not exist")
            features_df = pd.read_excel(self.DIST_DIR / PREPROCESSED_FEATURES_FILENAME)
        else:
            features_df = self.setup_matches_features(
                matches, time_spread=TMP_MONTH * 6
            )

        train_data: pd.DataFrame
        test_data: pd.DataFrame

        train_data = features_df[: int(len(features_df) * 0.7)]
        test_data = features_df[int(len(features_df) * 0.7) :]

        # train_data, test_data = train_test_split(
        #     features_df,
        #     test_size=0.3,
        # )

        if preprocessed_na_filler:
            if not os.path.exists(self.DIST_DIR / NA_FILLER_FILENAME):
                raise FileExistsError("NA Filler file does not exist")
            na_filler = pd.read_excel(self.DIST_DIR / NA_FILLER_FILENAME)
        else:
            na_filler = self.setup_na_filler(train_data)

        train_data = train_data.fillna(na_filler)
        test_data = test_data.fillna(na_filler)

        X_train = train_data.drop(columns=[TARGET])
        y_train = train_data[TARGET]
        X_test = test_data.drop(columns=[TARGET])
        y_test = test_data[TARGET]

        model = RandomForestClassifier(n_estimators=100)
        model.fit(X_train, y_train)
        self.save_model(model)

        self.estimate_model(model, X_test, y_test)

    def estimate_model(
        self,
        model: RandomForestClassifier,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ):
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"Model Accuracy: {accuracy:.2f}")


class StandardPredictor(StandardML):
    def __init__(
        self,
        sport: SportType,
        data: BaseDataInterface,
        na_filler: pd.Series | None = None,
        model: RandomForestClassifier | None = None,
    ) -> None:
        super().__init__(sport, data)

        self.na_filler = na_filler
        self.model = model

        self.initialize()

    def initialize(self) -> None:
        if not os.path.exists(self.DIST_DIR / NA_FILLER_FILENAME):
            raise FileExistsError("NA Filler file does not exist")
        if not os.path.exists(self.DIST_DIR / MODEL_FILENAME):
            raise FileExistsError("Model file does not exists")

        self.na_filler = pd.read_excel(self.DIST_DIR / NA_FILLER_FILENAME, index_col=0)
        self.model = self.upload_model()

    async def predict(self, match: MatchSDM):
        code_team1 = match.description.code_t1
        code_team2 = match.description.code_t2

        match_filter = MatchFilter(team_codes=[code_team1, code_team2])
        matches = await self.data.get_filtered_matches(match_filter)
        stats_bt, matches_bt, stats_keys = self.group_by_team(matches)

        features = self.setup_match_features(
            match,
            time_spread=TMP_MONTH * 6,
            stats_by_teams=stats_bt,
            matches_by_teams=matches_bt,
            stats_keys=stats_keys,
        )
        features = pd.DataFrame([features])

        for stname in self.na_filler.index:
            if stname not in features:
                features[stname] = None

        features = features[self.na_filler.index.tolist()]
        features = features.fillna(self.na_filler)

        predict = self.model.predict_proba(features)
        return predict[0]
