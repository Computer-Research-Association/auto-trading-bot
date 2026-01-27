import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Auto Trading Bot API")

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"DEBUG_REQ: {request.method} {request.url}")
    response = await call_next(request)
    print(f"DEBUG_RES: {response.status_code}")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router) 

@app.get("/")
def root():
    return {"message": "THIS IS REAL MAIN.PY 12345"}
