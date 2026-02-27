"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.ingestion import router as ingestion_router
from app.api.routes.scoring import router as scoring_router
from app.api.routes.decision import router as decision_router
from app.api.routes.loans import router as loans_router
from app.api.routes.chat import router as chat_router

app = FastAPI(title="LendSynthetix", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ingestion_router, prefix="/api")
app.include_router(scoring_router, prefix="/api")
app.include_router(decision_router, prefix="/api")
app.include_router(loans_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
