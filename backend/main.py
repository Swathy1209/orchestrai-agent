"""
server.py — OrchestrAI FastAPI Server
Real-Time Interactive Interview Coach API

Run locally:
    uvicorn backend.server:app --reload --port 8000

API Docs:
    http://localhost:8000/docs
"""

from __future__ import annotations

import logging
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.practice_routes import router as practice_router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("OrchestrAI.Server")

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="OrchestrAI Practice API",
    description=(
        "Real-Time AI Interview Coach — powered by Google Gemini.\n\n"
        "Ask interview questions in Tamil or English and receive:\n"
        "- Professional interview answers\n"
        "- Simplified practice versions\n"
        "- Confidence tips\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — allow practice HTML pages (hosted on GitHub Pages) to call this API ─
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production, restrict to your GitHub Pages domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(practice_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "OrchestrAI Practice API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health":     "GET  /practice/health",
            "ask":        "POST /practice/{company}/{role}/ask",
        },
    }
