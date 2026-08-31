from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from flood_pipeline import analyze_flood


app = FastAPI(
    title="TerraWatch API",
    description="AI-powered live flood detection using Sentinel-1 and Flood V3"
)


# ==========================================
# CORS
# Allow React frontend to communicate with API
# ==========================================

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


# ==========================================
# ROOT
# ==========================================

@app.get("/")
def root():
    return {
        "message": "TerraWatch API is running",
        "system": "Flood V3 + Live Sentinel-1"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():
    return {
        "status": "online",
        "services": {
            "backend": "connected",
            "ai_model": "Flood V3 ready",
            "satellite": "Google Earth Engine connected",
            "weather": "connected"
        }
    }


# ==========================================
# REAL AI FLOOD ANALYSIS
# ==========================================

@app.get("/analyze")
def analyze(latitude: float, longitude: float):

    try:
        # This now runs the REAL pipeline:
        # Live Sentinel-1 → preprocessing → Flood V3 U-Net
        result = analyze_flood(
            latitude=latitude,
            longitude=longitude
        )

        return result

    except Exception as error:
        print("\nTERRAWATCH ANALYSIS ERROR:")
        print(error)

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )