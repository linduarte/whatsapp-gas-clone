# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes

app = FastAPI(
    title="WhatsApp Gas Consumption API",
    description="API for managing gas consumption data and WhatsApp automation",
    version="1.0.0",
)

app.add_middleware(
    # pyrefly: ignore  # bad-argument-type
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "WhatsApp Gas Consumption API is running!"}
