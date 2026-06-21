# Parking Congestion Intelligence System

AI-driven detection of illegal parking hotspots and automated enforcement prioritization for Bengaluru traffic police.

**Live demo:** https://parking-congestion-intelligence-system.streamlit.app/
**Backend API:** https://parking-congestion-intelligence-system.onrender.com

---

## Problem

On-street illegal and spillover parking near commercial areas, metro stations, and junctions chokes carriageways and intersections across Bengaluru. Today:

- Enforcement is **patrol-based and reactive**, not data-driven.
- There is **no heatmap or scoring system** showing where parking violations are concentrated or how severe their impact is.
- Police have **no way to prioritize** which zones need enforcement attention first.


---

## Solution

A data pipeline + API + dashboard that ingests raw parking violation records and turns them into a **ranked, explainable list of enforcement priority zones**, visualized on an interactive map.

Given a violation record (location, vehicle, violation type, timestamp), the system:

1. Cleans and validates the raw data
2. Groups violations into physical **hotspots** (junctions or road segments)
3. Scores each hotspot using a weighted **Risk Score** combining violation volume, severity, recurrence, and vehicle impact
4. Ranks hotspots and assigns a **priority tier** (CRITICAL / HIGH / MEDIUM / LOW / VERY LOW)
5. Serves this through a REST API
6. Visualizes it on an interactive map dashboard with a searchable, sortable priority table and per-zone drilldown
---

## Approach & Methodology
### Data pipeline (3 stages)

**Stage 1 — `preprocess.py`**
Raw CSV (298,450 rows) → cleaned dataset:
- Filters out records the source system itself marked `rejected` or `duplicate` via `validation_status` (~50K rows removed) — this was a deliberate fix, since these are records the police already determined were invalid, and including them would have inflated hotspot scores with non-violations.
- Drops exact duplicate rows.
- Validates latitude/longitude are within real coordinate bounds.
- Drops rows with **neither** a usable `location` string **nor** a `junction_name` — these have no spatial identity to group by and were previously collapsing into a fake "NAN" hotspot.
- Parses `created_datetime`; extracts hour, day name, month, weekend flag.
- Standardizes text columns (strip whitespace, etc.).

**Stage 2 — `hotspot_calc.py`**
Cleaned data → aggregated hotspots:
- Each violation is assigned to a **hotspot**: the named junction if `junction_name` isn't "No Junction," otherwise a normalized version of the `location` string (case/punctuation/whitespace-insensitive, to reduce duplicate hotspots caused by minor text formatting differences in the source data).
- **Severity score** (1–5) is computed per violation from its `violation_type`, covering all 27 distinct violation types present in the dataset — from low-severity (`NO PARKING`) to high-severity (`JUMPING TRAFFIC SIGNAL`, `AGAINST ONE WAY/NO ENTRY`).
- **Vehicle impact score** (1–5) is computed per violation, preferring the corrected `updated_vehicle_type` field when present (human-reviewed correction) and falling back to the original `vehicle_type` otherwise.
- Violations are grouped by hotspot and aggregated: total violation count, average severity, average vehicle impact, number of distinct days with activity (`recurrence_days`), and mean coordinates.

**Stage 3 — `risk_calc.py`**
Aggregated hotspots → ranked, prioritized zones:
- Filters out low-signal hotspots with fewer than 50 violations (noise reduction).
- Normalizes (Min-Max scaling, 0–100) four features: log-scaled violation count, average severity, average vehicle impact, recurrence days.
- Computes a composite **Risk Score**:

  ```
  risk_score = 0.80 × violations_norm
              + 0.10 × severity_norm
              + 0.05 × recurrence_norm
              + 0.05 × vehicle_norm
  ```

  Volume is weighted most heavily (80%) because the problem statement asks specifically about **traffic flow / congestion impact**, which is driven more by how often and how persistently a location is obstructed than by the danger classification of the violation type. Severity, recurrence, and vehicle type act as differentiating signals among high-volume zones rather than primary drivers.

- Assigns a **priority tier** using **percentile-based cutoffs** (top 10% = CRITICAL, next 20% = HIGH, next 30% = MEDIUM, next 25% = LOW, remainder = VERY LOW) rather than fixed score thresholds — this makes the tiering robust to the actual shape of the score distribution instead of breaking down if scores cluster unexpectedly.

### Serving layer

A FastAPI backend reads the final `ranked_zones.csv` and `cleaned.csv` once at startup and exposes them via REST endpoints. A Streamlit frontend calls these endpoints to render the interactive map, stats summary, sortable priority table, and per-hotspot drilldown.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data processing | Python, pandas, NumPy |
| Scoring / normalization | scikit-learn (`MinMaxScaler`) |
| Backend API | FastAPI, Uvicorn |
| Frontend | Streamlit |
| Mapping | Folium, streamlit-folium (Leaflet under the hood) |
| Exploration | Jupyter Notebook |
| Hosting | Render (backend), Streamlit Community Cloud (frontend) |

---

## Project Structure

```
GridLock_Round2/
├── backend/
│   ├── __init__.py
│   ├── app.py                  # FastAPI app 
│   └── services/
│       ├── __init__.py
│       ├── preprocess.py       # Stage 1: clean raw data
│       ├── hotspot_calc.py     # Stage 2: aggregate into hotspots
│       └── risk_calc.py        # Stage 3: score and rank
├── frontend/
│   └── app.py                  # Streamlit dashboard
├── data/
│   ├── raw/                    # Place jan_to_may_police_violations.csv here
│   └── processed/              # Pipeline outputs land here
├── notebook/
│   └── eda.ipynb               # Exploratory data analysis
├── requirements.txt
├── .gitignore
```

---

## How to Run Locally

### Prerequisites
- Python 3.9+
- The raw dataset
### 1. Setup

```bash
git clone <repo-url>
cd GridLock_Round2
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Add the dataset

Place the raw CSV at:
```
data/raw/jan_to_may_police_violations.csv
```

### 3. Run the pipeline (in order)

```bash
cd backend/services
python preprocess.py      # → data/processed/cleaned.csv
python hotspot_calc.py    # → data/processed/hotspot_scores.csv
python risk_calc.py       # → data/processed/ranked_zones.csv
```

### 4. Start the backend

```bash
cd ../..
uvicorn backend.app:app --reload --port 8000
```
Verify: open `http://127.0.0.1:8000/stats` — should return JSON.

### 5. Start the frontend

In a second terminal:
```bash
streamlit run frontend/app.py
```
Note: `frontend/app.py` currently points `API_URL` at the deployed Render backend. To run fully locally, change it to `http://127.0.0.1:8000` before starting Streamlit.

---

## API Reference

Base URL (deployed): `https://parking-congestion-intelligence-system.onrender.com`

| Endpoint | Description |
|---|---|
| `GET /` | Health check |
| `GET /stats` | Summary metrics — total violations, hotspot count, critical zone count, top zone |
| `GET /map-data` | All ranked zones with coordinates, for map rendering |
| `GET /top-zones?limit=20` | Top N zones with full scoring breakdown |
| `GET /zone/{rank}` | Single zone by rank |
| `GET /search?query=...` | Substring search on hotspot name |
| `GET /critical-zones` | All zones tagged CRITICAL |
| `GET /priority-summary` | Count of zones per priority tier |

Interactive API docs available at `/docs` (FastAPI auto-generated Swagger UI).

---

## Data Notes

- Source: organizer-provided dataset, ~298,450 raw violation records (Bengaluru Traffic Police, BTP), shared via private link.
- The raw CSV is **excluded** from version control.
---

