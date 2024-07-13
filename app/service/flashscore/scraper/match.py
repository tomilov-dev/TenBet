import re
import sys
import asyncio
from pprint import pprint
from pathlib import Path
from bs4 import BeautifulSoup as soup


ROOT_DIR = Path(__file__).parent.parent.parent.parent
sys.path.append(str(ROOT_DIR))


from model.service import MatchSDM, MatchDescriptionSDM, TimeScoreSDM
from manager.service import FlashScoreMatchScraperInterface
from service.flashscore.common import (
    FlashScoreScraper,
    SportType,
    SPORT,
    StatusCode,
    TournamentNameParser,
)


STATUS_RX = re.compile(r'\{"DB":(\d+)\}')

PC_RX = re.compile(r"(\d+)\%")
PCD_PX = re.compile(r"(\d+)\s*\/\s*(\d+)")


class MatchParser:
    def __init__(self, sport: SportType) -> None:
        self.sport = sport

    def code3(self, status: str) -> bool:
        return status == StatusCode.get("3")

    def code10(self, status: str) -> bool:
        return status == StatusCode.get("10")

    def code11(self, status: str) -> bool:
        return status == StatusCode.get("11")

    def get_description(
        self,
        match: MatchSDM,
        response: str,
    ) -> MatchSDM:
        if response:
            s = soup(response, "lxml")
            tournament_fullname = s.find("meta", {"name": "og:description"}).get(
                "content"
            )

            tournament_name_parsed = TournamentNameParser.parse(tournament_fullname)

            full_names = s.find("title").text.split(" | ")[1].split(" - ")
            full_name1 = full_names[0].strip()
            full_name2 = full_names[1].strip()

            short_names = re.findall(r'"short_name":"(.+?)"', response)
            short_name1 = short_names[0]
            short_name2 = short_names[1]

            code_t1 = re.search(r'"home":\[\{"id":"(.*?)",', response).group(1)
            code_t2 = re.search(r'"away":\[\{"id":"(.*?)",', response).group(1)

            winner = re.findall(r'"AZ":"{,1}(\d+)', response)
            winner = int(winner[0].strip()) if winner else None

            reason = re.findall(r'"DM":"(.+?)(?<=")', response)[0].strip()

            start_date = re.findall(r'"DC":"{0,1}(\d+)"{0,1}', response)[0].strip()
            end_date = re.findall(r'"DD":"{0,1}(\d+)"{0,1}', response)[0].strip()

            infobox = response.split('"DM":"')[1]
            infobox = infobox.split('"},{')[0]

            if self.code3(match.status):
                match_score1 = int(re.findall(r'"DE":"{0,1}(\d+)', response)[0])
                match_score2 = int(re.findall(r'"DF":"{0,1}(\d+)', response)[0])
            elif self.code10(match.status) or self.code11(match.status):
                match_score1 = int(re.findall(r'"DG":"{0,1}(\d+)', response)[0])
                match_score2 = int(re.findall(r'"DH":"{0,1}(\d+)', response)[0])
            else:
                match_score1 = None
                match_score2 = None

            description = MatchDescriptionSDM(
                **tournament_name_parsed.model_dump(),
                code_t1=code_t1,
                code_t2=code_t2,
                full_name_t1=full_name1,
                full_name_t2=full_name2,
                short_name_t1=short_name1,
                short_name_t2=short_name2,
                winner=winner,
                reason=reason,
                start_date=int(start_date),
                end_date=int(end_date),
                score_t1=match_score1,
                score_t2=match_score2,
                infobox=infobox,
            )
            match.description = description

        return match

    def get_times_score(
        self,
        match: MatchSDM,
        response: str,
    ) -> MatchSDM:
        time_scores: list[TimeScoreSDM] = []

        time_sets = re.findall(r"B.÷\d+.*?\d+:\d+¬", response)
        for time_set in time_sets:
            scores = re.findall(r"B.÷(\d+)", time_set)
            tiebreaks = re.findall(r"D.÷(\d+)", time_set)
            time = re.search(r"R.÷(\d+:\d+)", time_set)

            if scores:
                score_t1 = scores[0]
                score_t2 = scores[1]
            else:
                score_t1 = None
                score_t2 = None

            if tiebreaks:
                tiebreak_t1 = tiebreaks[0]
                tiebreak_t2 = tiebreaks[1]
            else:
                tiebreak_t1 = None
                tiebreak_t2 = None

            if time:
                time = time.group(1).split(":")
                htime = int(time[0].strip()) * 60
                mtime = int(time[1].strip())
                time = htime + mtime
            else:
                time = None

            time_score = TimeScoreSDM(
                score_t1=score_t1,
                score_t2=score_t2,
                tiebreak_t1=tiebreak_t1,
                tiebreak_t2=tiebreak_t2,
                playtime=time,
            )
            time_scores.append(time_score)

        total_playtime = re.findall(r"R.÷(\d+:\d+)", response)
        if total_playtime:
            total_playtime = total_playtime[-1].split(":")
            htime = int(total_playtime[0].strip()) * 60
            mtime = int(total_playtime[1].strip())
            total_playtime = htime + mtime
        else:
            total_playtime = None

        for i in range(len(time_scores), 5):
            time_scores.append(None)

        match.playtime = total_playtime
        match.time1 = time_scores[0]
        match.time2 = time_scores[1]
        match.time3 = time_scores[2]
        match.time4 = time_scores[3]
        match.time5 = time_scores[4]

        return match

    def preprocess_stat(
        self,
        value: int,
    ) -> int | tuple[int, int]:
        if "%" in value and "(" in value:
            out1, out2 = PCD_PX.findall(value)[0]
            return [int(out1), int(out2)]
        elif "%" in value:
            output = float(PC_RX.search(value).group(1))
        else:
            output = float(value)
        return output

    def get_statistics(
        self,
        match: MatchSDM,
        response: str,
    ) -> MatchSDM:
        stat_splitter = self.sport.stat_splitter

        statistics1 = {}
        statistics2 = {}

        stat_parts_by_iter = response.split("SE÷")[1:]
        for iter in range(len(stat_parts_by_iter)):
            stat_part = stat_parts_by_iter[iter]
            stats = stat_part.split(stat_splitter)

            stat_names, stats1, stats2 = [], [], []
            for stat in stats[1:]:
                stat_names.append(stat.split("¬SH÷")[0])
                stats1.append(stat.split("¬SH÷")[1].split("¬SI÷")[0])
                stats2.append(stat.split("¬SI÷")[1].split("¬~")[0])

            stats1_time = {}
            stats2_time = {}
            for i in range(len(stat_names)):
                if iter == 0:
                    time_name = "match"
                else:
                    time_name = f"time{iter}"

                stats1_time[stat_names[i]] = self.preprocess_stat(stats1[i])
                stats2_time[stat_names[i]] = self.preprocess_stat(stats2[i])

            statistics1[time_name] = stats1_time
            statistics2[time_name] = stats2_time

        match.statistics1 = statistics1
        match.statistics2 = statistics2

        return match

    def get_status(
        self,
        match: MatchSDM,
        response: str | None,
    ) -> MatchSDM:
        status = StatusCode.undefined()
        if response:
            status = StatusCode.extract(STATUS_RX, response)

        match.status = status
        return match


class MatchScraper(FlashScoreMatchScraperInterface, FlashScoreScraper):
    def __init__(
        self,
        sport: SportType,
        proxy: str = None,
        debug: bool = False,
    ) -> None:
        FlashScoreMatchScraperInterface.__init__(self, sport)
        FlashScoreScraper.__init__(self, proxy, debug)

        self.parser = MatchParser(sport)

    async def scrape_description(
        self,
        match: MatchSDM,
        code: str,
    ) -> MatchSDM:
        url = f"https://www.flashscore.co.uk/match/{code}/#/match-summary"
        response = await self.request(url)
        if response is None:
            match.error = True
            return match

        match = self.parser.get_status(match, response)
        match = self.parser.get_description(match, response)

        return match

    async def scrape_score(
        self,
        match: MatchSDM,
        code: str,
    ) -> MatchSDM:
        if StatusCode.finished(match.status):
            url = f"https://d.flashscore.co.uk/x/feed/df_sur_1_{code}"
            response = await self.request(url)

            if response is None:
                match.error = True
                return match

            match = self.parser.get_times_score(match, response)

        return match

    async def scrape_statistics(
        self,
        match: MatchSDM,
        code: str,
    ) -> MatchSDM:
        if StatusCode.finished(match.status):
            st = self.sport.stat_prefix
            url = f"https://d.flashscore.co.uk/x/feed/df_{st}_1_{code}"
            response = await self.request(url)

            if response is None:
                match.error = True
                return match

            match = self.parser.get_statistics(match, response)

        return match

    async def scrape(self, code: str) -> MatchSDM:
        match = MatchSDM(code=code)

        match = await self.scrape_description(match, code)
        match = await self.scrape_score(match, code)
        match = await self.scrape_statistics(match, code)

        return match


async def test_tennis_men():
    scraper = MatchScraper(sport=SPORT.TENNIS_MEN)
    code = "21vkvxmJ"

    data = await scraper.scrape(code)
    print(data)


async def test_tennis_women():
    scraper = MatchScraper(sport=SPORT.TENNIS_WOMEN)
    code = "UVpnRkml"

    data = await scraper.scrape(code)
    print(data)


async def test_football():
    scraper = MatchScraper(sport=SPORT.FOOTBALL)
    code = "GziuczET"

    data = await scraper.scrape(code)
    print(data)


async def test_hockey():
    scraper = MatchScraper(sport=SPORT.HOCKEY)
    code = "ro9gcXlC"

    data = await scraper.scrape(code)
    print(data)


async def test_backetball():
    scraper = MatchScraper(sport=SPORT.BASKETBALL)
    code = "CdcbfwIf"

    data = await scraper.scrape(code)
    print(data)


if __name__ == "__main__":
    asyncio.run(test_football())
