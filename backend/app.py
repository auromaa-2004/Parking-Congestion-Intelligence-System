from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path

app = FastAPI(
    title="Parking Congestion Intelligence API",
    description="AI-powered parking hotspot detection and enforcement prioritization",
    version="1.0.0"
)

# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# DATA PATHS
# --------------------------------------------------

RANKED_FILE = Path("data/processed/ranked_zones.csv")
CLEANED_FILE = Path("data/processed/cleaned.csv")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

ranked_df = pd.read_csv(RANKED_FILE)
cleaned_df = pd.read_csv(CLEANED_FILE)

# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Parking Congestion Intelligence API",
        "status": "running"
    }


# --------------------------------------------------
# DASHBOARD STATS
# --------------------------------------------------

@app.get("/stats")
def get_stats():

    return {
        "total_violations": int(len(cleaned_df)),

        "total_hotspots": int(len(ranked_df)),

        "critical_zones": int(
            (ranked_df["priority"] == "CRITICAL").sum()
        ),

        "high_priority_zones": int(
            (ranked_df["priority"] == "HIGH").sum()
        ),

        "top_zone": ranked_df.iloc[0]["hotspot_name"],

        "highest_risk_score": float(
            ranked_df["risk_score"].max()
        )
    }


# --------------------------------------------------
# TOP ZONES
# --------------------------------------------------

@app.get("/top-zones")
def get_top_zones(limit: int = 20):

    return (
        ranked_df
        .head(limit)
        .to_dict(orient="records")
    )


# --------------------------------------------------
# ZONE BY RANK
# --------------------------------------------------

@app.get("/zone/{rank}")
def get_zone(rank: int):

    zone = ranked_df[
        ranked_df["rank"] == rank
    ]

    if len(zone) == 0:
        raise HTTPException(
            status_code=404,
            detail="Zone not found"
        )

    return zone.iloc[0].to_dict()


# --------------------------------------------------
# SEARCH HOTSPOT
# --------------------------------------------------

@app.get("/search")
def search_hotspot(query: str):

    results = ranked_df[
        ranked_df["hotspot_name"]
        .str.contains(
            query,
            case=False,
            na=False
        )
    ]

    return (
        results
        .head(20)
        .to_dict(orient="records")
    )


# --------------------------------------------------
# MAP DATA
# --------------------------------------------------

@app.get("/map-data")
def get_map_data():

    cols = [
        "rank",
        "hotspot_name",
        "hotspot_type",
        "latitude",
        "longitude",
        "risk_score",
        "priority",
        "violations",
        "recommendation"
    ]

    return (
        ranked_df[cols]
        .to_dict(orient="records")
    )


# --------------------------------------------------
# TOP CRITICAL ZONES
# --------------------------------------------------

@app.get("/critical-zones")
def get_critical_zones():

    critical = ranked_df[
        ranked_df["priority"] == "CRITICAL"
    ]

    return critical.to_dict(
        orient="records"
    )


# --------------------------------------------------
# PRIORITY DISTRIBUTION
# --------------------------------------------------

@app.get("/priority-summary")
def priority_summary():

    summary = (
        ranked_df["priority"]
        .value_counts()
        .to_dict()
    )

    return summary