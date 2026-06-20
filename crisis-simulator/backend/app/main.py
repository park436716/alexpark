from fastapi import FastAPI

from app.api.decisions import router as decisions_router
from app.api.facilitator import router as facilitator_router
from app.api.sessions import router as sessions_router

app = FastAPI(title="AI Crisis Simulator")
app.include_router(sessions_router, prefix="/api")
app.include_router(decisions_router, prefix="/api")
app.include_router(facilitator_router, prefix="/api")


@app.get("/")
def health_check():
    return {"status": "ok"}
