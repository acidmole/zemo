"""FastAPI application entry point for Space Station Zemo."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data.board_layout import BOARD_DATA
from app.routes.game_routes import router as game_router
from app.routes.save_routes import router as save_router

app = FastAPI(
    title="Space Station Zemo",
    description="Backend API for the Space Station Zemo board game",
    version="1.0.0",
)

# CORS: allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(game_router)
app.include_router(save_router)


@app.get("/")
def root() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "game": "Space Station Zemo"}


@app.get("/board")
def board() -> dict:
    """Board image, spaces (with drawing shapes) and connections."""
    return BOARD_DATA
