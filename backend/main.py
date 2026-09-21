from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import sys


# ============================================================
# BACKEND MODULE PATH
# ============================================================
# The project is started from:
# E:\Project\TerraWatch_Web
#
# Your existing pipeline files live inside:
# E:\Project\TerraWatch_Web\backend
#
# Add the backend folder to Python's import path so the
# existing absolute imports inside the pipeline files continue
# to work (for example: from flood_pipeline import ...).
# ============================================================

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


# ============================================================
# PIPELINE IMPORTS
# ============================================================

from flood_pipeline import analyze_flood
from landslide_pipeline import analyze_landslide


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="DisasterLens AI API",
    description=(
        "AI-powered multi-hazard disaster analysis using "
        "live satellite data, Flood V3 and Landslide V5"
    ),
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "DisasterLens AI API is running",
        "system": "Flood V3 + Landslide V5",
        "satellites": [
            "Sentinel-1",
            "Sentinel-2"
        ]
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "online",
        "services": {
            "backend": "connected",
            "flood_model": "Flood V3 ready",
            "landslide_model": "Landslide V5 ready",
            "satellite": "Google Earth Engine connected",
        }
    }


# ============================================================
# FLOOD ANALYSIS
# ============================================================

@app.get("/analyze/flood")
def analyze_flood_location(
    latitude: float,
    longitude: float
):
    """
    Run the existing Flood V3 live analysis.

    Pipeline:
        Location
            ↓
        Google Earth Engine
            ↓
        Sentinel-1 SAR
            ↓
        Flood V3 U-Net
            ↓
        Flood result
    """

    try:
        result = analyze_flood(
            latitude=latitude,
            longitude=longitude
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Flood analysis returned no result."
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        print()
        print("=" * 70)
        print("DISASTERLENS FLOOD API ERROR")
        print("=" * 70)
        print(type(error).__name__, ":", str(error))
        print("=" * 70)

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# LANDSLIDE ANALYSIS
# ============================================================

@app.get("/analyze/landslide")
def analyze_landslide_location(
    latitude: float,
    longitude: float
):
    """
    Run the existing Landslide V5 live analysis.

    Pipeline:
        Location
            ↓
        Google Earth Engine
            ↓
        Sentinel-2 + Cloud Probability
            +
        ALOS DEM + Slope
            ↓
        14-channel live image
            ↓
        Landslide V5 U-Net
            ↓
        Landslide result
    """

    try:
        result = analyze_landslide(
            latitude=latitude,
            longitude=longitude
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Landslide analysis returned no result."
            )

        return result

    except HTTPException:
        raise

    except Exception as error:
        print()
        print("=" * 70)
        print("DISASTERLENS LANDSLIDE API ERROR")
        print("=" * 70)
        print(type(error).__name__, ":", str(error))
        print("=" * 70)

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ============================================================
# COMBINED MULTI-HAZARD ANALYSIS
# ============================================================

@app.get("/analyze")
def analyze(
    latitude: float,
    longitude: float
):
    """
    Run BOTH hazard models for the same location.

    Flood and Landslide are intentionally handled
    independently so that one failure does not hide
    a successful result from the other model.
    """

    flood_result = None
    landslide_result = None

    # --------------------------------------------------------
    # FLOOD
    # --------------------------------------------------------

    try:
        flood_result = analyze_flood(
            latitude=latitude,
            longitude=longitude
        )

    except Exception as error:
        print()
        print("FLOOD ANALYSIS FAILED:")
        print(type(error).__name__, ":", str(error))

        flood_result = {
            "success": False,
            "error": str(error)
        }

    # --------------------------------------------------------
    # LANDSLIDE
    # --------------------------------------------------------

    try:
        landslide_result = analyze_landslide(
            latitude=latitude,
            longitude=longitude
        )

    except Exception as error:
        print()
        print("LANDSLIDE ANALYSIS FAILED:")
        print(type(error).__name__, ":", str(error))

        landslide_result = {
            "success": False,
            "error": str(error),
            "satellite": "Sentinel-2",
            "acquisition": None,
            "acquisition_date": None,
            "coverage": 0.0,
            "landslide_coverage_percent": 0.0,
            "mean_probability": 0.0,
            "max_probability": 0.0,
            "landslide_pixels": 0,
            "total_pixels": 16384,
            "risk": "UNKNOWN",
            "risk_level": "UNKNOWN",
            "mask": [[0] * 128 for _ in range(128)]
        }

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "success": (
            bool(flood_result and flood_result.get("success"))
            or
            bool(landslide_result and landslide_result.get("success"))
        ),

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "flood": flood_result,

        "landslide": landslide_result,

        "system": {
            "name": "DisasterLens AI",
            "hazards": [
                "Flood",
                "Landslide"
            ],
            "satellites": {
                "flood": "Sentinel-1",
                "landslide": "Sentinel-2"
            }
        }
    }


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
