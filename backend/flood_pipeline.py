import ee
import numpy as np
import torch
import torch.nn.functional as F

from flood_model import model, device
from gee_auth import initialize_gee as initialize_gee_auth


# ==========================================
# TERRAWATCH GOOGLE EARTH ENGINE PROJECT
# ==========================================

PROJECT_ID = "terrawatch-ai-506504"


# ==========================================
# FLOOD V3 LOCKED CONFIGURATION
# ==========================================

VV_MEAN = -10.4864
VV_STD = 4.2119

VH_MEAN = -17.3808
VH_STD = 4.8847

FLOOD_THRESHOLD = 0.35
PATCH_SIZE = 512


# ==========================================
# INITIALIZE GOOGLE EARTH ENGINE
# ==========================================

def initialize_gee():
    return initialize_gee_auth()

# ==========================================
# CREATE ANALYSIS REGION
# Approximately 5 km around selected point
# ==========================================

def create_analysis_region(latitude, longitude):

    half_size_degrees = 0.023

    return ee.Geometry.Rectangle([
        longitude - half_size_degrees,
        latitude - half_size_degrees,
        longitude + half_size_degrees,
        latitude + half_size_degrees
    ])


# ==========================================
# GET LATEST SENTINEL-1 VV + VH IMAGE
# ==========================================

def get_latest_sentinel_image(region):

    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(region)
        .filter(
            ee.Filter.listContains(
                "transmitterReceiverPolarisation",
                "VV"
            )
        )
        .filter(
            ee.Filter.listContains(
                "transmitterReceiverPolarisation",
                "VH"
            )
        )
        .filter(
            ee.Filter.eq(
                "instrumentMode",
                "IW"
            )
        )
        .filter(
            ee.Filter.eq(
                "orbitProperties_pass",
                "DESCENDING"
            )
        )
        .sort("system:time_start", False)
    )

    image = collection.first()

    # Check whether an image exists
    image_id = image.get("system:id").getInfo()

    if image_id is None:
        raise Exception(
            "No suitable Sentinel-1 imagery was found for this location."
        )

    image_date = (
        ee.Date(image.get("system:time_start"))
        .format("YYYY-MM-dd HH:mm:ss")
        .getInfo()
    )

    return (
        image.select(["VV", "VH"]).clip(region),
        image_date
    )


# ==========================================
# DOWNLOAD VV + VH PIXELS FROM GEE
# ==========================================

def get_image_array(image, region):

    sampled = image.sampleRectangle(
        region=region,
        defaultValue=-9999
    ).getInfo()

    properties = sampled.get("properties", {})

    if "VV" not in properties or "VH" not in properties:
        raise Exception(
            "Could not retrieve VV/VH satellite pixels."
        )

    vv = np.array(
        properties["VV"],
        dtype=np.float32
    )

    vh = np.array(
        properties["VH"],
        dtype=np.float32
    )

    return vv, vh


# ==========================================
# PREPROCESS FOR FLOOD V3 MODEL
# ==========================================

def preprocess_image(vv, vh):

    # Handle invalid values
    vv = np.nan_to_num(
        vv,
        nan=VV_MEAN,
        posinf=VV_MEAN,
        neginf=VV_MEAN
    )

    vh = np.nan_to_num(
        vh,
        nan=VH_MEAN,
        posinf=VH_MEAN,
        neginf=VH_MEAN
    )

    # Handle missing Earth Engine pixels
    vv[vv == -9999] = VV_MEAN
    vh[vh == -9999] = VH_MEAN

    # Stack VV + VH into two-channel image
    image = np.stack(
        [vv, vh],
        axis=0
    )

    tensor = torch.tensor(
        image,
        dtype=torch.float32
    ).unsqueeze(0)

    # Resize exactly to model input size
    tensor = F.interpolate(
        tensor,
        size=(PATCH_SIZE, PATCH_SIZE),
        mode="bilinear",
        align_corners=False
    )

    tensor = tensor.squeeze(0).cpu().numpy()

    vv = tensor[0]
    vh = tensor[1]

    # EXACT normalization used for Flood V3 training
    vv = (vv - VV_MEAN) / (VV_STD + 1e-8)
    vh = (vh - VH_MEAN) / (VH_STD + 1e-8)

    vv = np.nan_to_num(vv)
    vh = np.nan_to_num(vh)

    processed = np.stack(
        [vv, vh],
        axis=0
    )

    return torch.tensor(
        processed,
        dtype=torch.float32
    ).unsqueeze(0)


# ==========================================
# RUN FLOOD V3 AI MODEL
# ==========================================

def run_model(input_tensor):

    input_tensor = input_tensor.to(device)

    with torch.no_grad():

        logits = model(input_tensor)

        probabilities = torch.softmax(
            logits,
            dim=1
        )

        # Class 1 = Flood
        flood_probability = probabilities[:, 1, :, :]

        flood_mask = (
            flood_probability >= FLOOD_THRESHOLD
        )

    flood_probability = (
        flood_probability
        .squeeze()
        .cpu()
        .numpy()
    )

    flood_mask = (
        flood_mask
        .squeeze()
        .cpu()
        .numpy()
    )

    return flood_probability, flood_mask


# ==========================================
# DETERMINE ALERT LEVEL
# ==========================================

def calculate_alert(flood_percentage):

    if flood_percentage >= 20:
        return "HIGH", "ACTIVE FLOOD SIGNAL DETECTED"

    elif flood_percentage >= 5:
        return "MEDIUM", "POSSIBLE FLOODING DETECTED"

    return "LOW", "NO SIGNIFICANT FLOOD SIGNAL DETECTED"


# ==========================================
# MAIN TERRAWATCH FLOOD ANALYSIS
# ==========================================

def analyze_flood(latitude, longitude):

    print("\n" + "=" * 55)
    print("TERRAWATCH LIVE FLOOD ANALYSIS STARTED")
    print(f"Location: {latitude}, {longitude}")
    print("=" * 55)

    # Connect to Google Earth Engine
    if not initialize_gee():
        raise Exception(
            "Google Earth Engine could not be initialized."
        )

    # Create analysis area
    region = create_analysis_region(
        latitude,
        longitude
    )

    print("Fetching latest Sentinel-1 imagery...")

    # Fetch live Sentinel-1
    image, image_date = get_latest_sentinel_image(
        region
    )

    print(f"Satellite image date: {image_date}")
    print("Downloading VV + VH satellite data...")

    # Get satellite pixels
    vv, vh = get_image_array(
        image,
        region
    )

    print(
        f"Satellite data received: "
        f"VV {vv.shape}, VH {vh.shape}"
    )

    # Preprocess exactly like training
    input_tensor = preprocess_image(
        vv,
        vh
    )

    print("Running Flood V3 U-Net inference...")

    # Real AI inference
    flood_probability, flood_mask = run_model(
        input_tensor
    )

    # Calculate predicted flood coverage
    flood_percentage = float(
        np.mean(flood_mask) * 100
    )

    # Average flood probability
    average_probability = float(
        np.mean(flood_probability) * 100
    )

    alert_level, status = calculate_alert(
        flood_percentage
    )

    print(
        f"Flood coverage: {flood_percentage:.2f}%"
    )
    print(
        f"Average probability: "
        f"{average_probability:.2f}%"
    )
    print(f"Alert level: {alert_level}")
    print("=" * 55 + "\n")

    # Return data to FastAPI
    return {
        "success": True,

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "satellite_status": "LIVE SENTINEL-1 ANALYZED",

        "satellite_image_date": image_date,

        "flood_coverage_percentage": round(
            flood_percentage,
            2
        ),

        "model_confidence": round(
            average_probability,
            2
        ),

        # These are retained so your existing
        # React frontend can continue working
        "weather_risk_score": round(
            flood_percentage,
            2
        ),

        "weather_risk_level": alert_level,

        "overall_status": status,

        "alert_level": alert_level,

        # Actual pixel-level Flood V3 segmentation mask.
        # The analysis region is the same rectangle used to fetch
        # Sentinel-1 pixels, so these bounds are used by the map
        # to place the mask over the satellite image.
        "flood_mask": flood_mask.astype(np.uint8).tolist(),
        "flood_bounds": [
            [latitude - 0.023, longitude - 0.023],
            [latitude + 0.023, longitude + 0.023]
        ]
    }