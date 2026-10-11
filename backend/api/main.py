from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.database.database import get_db, engine, Base
from backend.services.analytics_service import AnalyticsService

# Initialize tables if not exist (useful for dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Government Welfare Scheme Awareness Gap Miner API",
    description="API for the NLP analytics research platform.",
    version="1.0.0"
)

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development. Configure for production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Welfare Awareness Gap Miner API"}

@app.get("/api/dashboard/overview")
def get_overview(db: Session = Depends(get_db)):
    svc = AnalyticsService(db)
    return svc.get_overview_metrics()

@app.get("/api/schemes")
def get_schemes(db: Session = Depends(get_db)):
    svc = AnalyticsService(db)
    return svc.get_scheme_metrics()

@app.get("/api/regions")
def get_regions(db: Session = Depends(get_db)):
    svc = AnalyticsService(db)
    return svc.get_geographic_metrics()

if __name__ == "__main__":
    import uvicorn
    # Make sure to run from project root: python -m backend.api.main
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
