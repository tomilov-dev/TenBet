from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.tennis_men import router as tennis_men_router
from web.tennis_women import router as tennis_women_router


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["X-Requested-With", "Content-Type", "Authorization"],
)

app.include_router(tennis_men_router, prefix="/tennis_men")
app.include_router(tennis_women_router, prefix="/tennis_women")
