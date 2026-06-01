import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.sites import router as sites_router
from routers.stats import router as stats_router


app = FastAPI(
	title="DustWatch API",
	version="0.1.0",
	description="Satellite-AI platform for urban construction dust accountability",
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:3000", "http://localhost:5173"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(sites_router, prefix="/api")
app.include_router(stats_router, prefix="/api")


@app.get("/")
def root() -> dict:
	return {"status": "ok", "project": "DustWatch", "version": "0.1.0"}


@app.get("/health")
def health() -> dict:
	return {"status": "healthy"}
