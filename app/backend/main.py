"""
FastAPI backend for Dual AI Assistant.
Entry point: uvicorn app.backend.main:app --reload
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from .routes import router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.getLogger(__name__).info("Dual Assistant API starting up")
    yield
    logging.getLogger(__name__).info("Dual Assistant API shutting down")


app = FastAPI(
    title="Dual AI Assistant API",
    description="OSS (Qwen2.5-0.5B-Instruct) vs Frontier (Gemini 2.5 Flash) comparison platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
