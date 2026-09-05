from fastapi import FastAPI
from app.db import engine
from app.models import Base

app = FastAPI(title="Telegram Food Delivery Bot")

@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return {"status": "ok"}
    except Exception:
        return {"status": "degraded"}
