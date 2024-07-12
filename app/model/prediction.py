from pydantic import BaseModel


class MatchPredictionHA(BaseModel):
    code: str

    win_predict: int
    probability_t1: float
    probability_t2: float


class MatchPrediction1x2(MatchPredictionHA):
    probability_x: float
