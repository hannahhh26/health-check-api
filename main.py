import os

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/info")
def get_info():
    return {"environment": os.getenv("APP_ENV", "local")}