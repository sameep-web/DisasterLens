# ============================================================
# TERRAWATCH AI
# FINAL LIVE LANDSLIDE PIPELINE
# ============================================================

import datetime

import cv2
import ee
import numpy as np


# ============================================================
# GOOGLE EARTH ENGINE
# ============================================================

PROJECT_ID = "terrawatch-ai-506504"

ee.Initialize(project=PROJECT_ID)


# ============================================================
# CONFIG
# ============================================================

S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
S2_CLOUD_COLLECTION = "COPERNICUS/S2_CLOUD_PROBABILITY"
ALOS_COLLECTION = "JAXA/ALOS/AW3D30/V4_1"

SEARCH_DAYS = 30
MAX_CLOUD_PROBABILITY = 60

IMAGE_SIZE = 128

TARGET_CRS = "EPSG:32643"
TARGET_SCALE = 10


# ============================================================
# EXACT 14 CHANNEL ORDER
# ============================================================

CHANNEL_NAMES = [
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "B6",
    "B7",
    "B8",
    "B9",
    "B10",
    "B11",
    "B12",
    "SLOPE",
    "DEM",
]


# ============================================================
# V5 SELECTED CHANNELS
# ============================================================

SELECTED_CHANNELS = [
    0,
    1,
    2,
    3,
    4,
    10,
    11,
    12,
    13,
]


# ============================================================
# DATE RANGE
# ============================================================

def get_date_range():

    now = datetime.datetime.now(
        datetime.timezone.utc
    )

    end_date = ee.Date(
        now.isoformat()
    )

    start_date = end_date.advance(
        -SEARCH_DAYS,
        "day"
    )

    return start_date, end_date


# ============================================================
# CLOUD MASK
# ============================================================

def apply_cloud_mask(image):

    cloud_image = ee.Image(
        image.get(
            "cloud_probability"
        )
    )

    probability = (
        cloud_image
        .select("probability")
    )

    mask = probability.lt(
        MAX_CLOUD_PROBABILITY
    )

    return (
        ee.Image(image)
        .updateMask(mask)
    )


# ============================================================
# ALOS DEM + SLOPE
# ============================================================
#
# THIS IS THE IMPORTANT FIX.
#
# Google Earth Engine documentation specifically recommends
# calculating slope using the projection of an individual
# ALOS tile rather than the projection of the mosaic.
#
# ============================================================

def build_alos():

    print()
    print(
        "Loading ALOS AW3D30..."
    )

    collection = (
        ee.ImageCollection(
            ALOS_COLLECTION
        )
        .select("DSM")
    )

    count = (
        collection
        .size()
        .getInfo()
    )

    print(
        "ALOS images:",
        count
    )

    if count == 0:

        raise RuntimeError(
            "No ALOS AW3D30 data found."
        )

    # --------------------------------------------------------
    # Get native projection from first ALOS tile.
    # --------------------------------------------------------

    native_projection = (
        collection
        .first()
        .select("DSM")
        .projection()
    )

    # --------------------------------------------------------
    # Mosaic DEM using native projection.
    # --------------------------------------------------------

    dem = (
        collection
        .mosaic()
        .setDefaultProjection(
            native_projection
        )
    )

    # --------------------------------------------------------
    # CORRECT SLOPE
    # --------------------------------------------------------

    slope = (
        ee.Terrain
        .slope(
            dem
        )
        .rename(
            "SLOPE"
        )
    )

    return dem, slope


# ============================================================
# BUILD 14 CHANNEL STACK
# ============================================================

def build_14_channel_stack(
    s2_image,
    dem,
    slope
):

    # --------------------------------------------------------
    # Sentinel-2 SR bands available from SR collection.
    #
    # B10 is not available in Sentinel-2 SR.
    #
    # V5 DOES NOT USE CHANNEL 9.
    # --------------------------------------------------------

    optical = (
        s2_image
        .select([
            "B1",
            "B2",
            "B3",
            "B4",
            "B5",
            "B6",
            "B7",
            "B8",
            "B9",
            "B11",
            "B12",
        ])
        .divide(
            10000.0
        )
        .multiply(
            10.0
        )
    )

    # --------------------------------------------------------
    # Placeholder only for unused V5 channel 9.
    #
    # V5 selected channels are:
    # 0,1,2,3,4,10,11,12,13
    #
    # Therefore this value NEVER reaches the model.
    # --------------------------------------------------------

    b10_placeholder = (
        optical
        .select("B9")
        .rename("B10")
    )

    # --------------------------------------------------------
    # DEM
    # --------------------------------------------------------

    dem_scaled = (
        dem
        .divide(
            1000.0
        )
        .rename(
            "DEM"
        )
    )

    # --------------------------------------------------------
    # EXACT 14 CHANNELS
    # --------------------------------------------------------

    image = ee.Image.cat([

        optical.select("B1"),

        optical.select("B2"),

        optical.select("B3"),

        optical.select("B4"),

        optical.select("B5"),

        optical.select("B6"),

        optical.select("B7"),

        optical.select("B8"),

        optical.select("B9"),

        b10_placeholder,

        optical.select("B11"),

        optical.select("B12"),

        slope,

        dem_scaled,
    ])

    image = image.rename(
        CHANNEL_NAMES
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Do NOT call reproject() on the complete stack.
    #
    # setDefaultProjection gives sampleRectangle a common
    # 10m output grid without forcing the whole computation.
    # --------------------------------------------------------

    image = (
        image
        .setDefaultProjection(
            crs=TARGET_CRS,
            scale=TARGET_SCALE
        )
    )

    return image


# ============================================================
# SAMPLE RECTANGLE
# ============================================================

def sample_rectangle(
    image,
    region
):

    print()
    print(
        "Sampling rectangular pixel grid..."
    )

    result = (
        image
        .sampleRectangle(
            region=region,
            defaultValue=0
        )
        .getInfo()
    )

    print(
        "GEE result type:",
        result.get("type")
    )

    properties = result.get(
        "properties",
        {}
    )

    print(
        "Returned bands:",
        list(
            properties.keys()
        )
    )

    if not properties:

        raise RuntimeError(
            "GEE returned no properties."
        )

    arrays = []

    for channel in CHANNEL_NAMES:

        if channel not in properties:

            raise RuntimeError(
                "Missing GEE channel: "
                + channel
            )

        arr = np.asarray(
            properties[channel],
            dtype=np.float32
        )

        print(
            f"{channel:<6} shape = "
            f"{arr.shape}"
        )

        if arr.ndim != 2:

            raise RuntimeError(
                f"{channel} is not 2D: "
                f"{arr.shape}"
            )

        arrays.append(
            arr
        )

    # --------------------------------------------------------
    # Align all bands
    # --------------------------------------------------------

    height = max(
        arr.shape[0]
        for arr in arrays
    )

    width = max(
        arr.shape[1]
        for arr in arrays
    )

    print()
    print(
        "Target GEE grid:",
        height,
        "x",
        width
    )

    aligned = []

    for arr in arrays:

        if arr.shape != (
            height,
            width
        ):

            arr = cv2.resize(
                arr,
                (
                    width,
                    height
                ),
                interpolation=cv2.INTER_LINEAR
            )

        aligned.append(
            arr
        )

    image = np.stack(
        aligned,
        axis=-1
    )

    return image


# ============================================================
# CLEAN INVALID VALUES
# ============================================================

def clean_image(
    image
):

    image = np.asarray(
        image,
        dtype=np.float32
    )

    for i in range(
        image.shape[-1]
    ):

        band = image[
            :,
            :,
            i
        ]

        valid = np.isfinite(
            band
        )

        if not valid.any():

            raise RuntimeError(
                "No valid values in "
                + CHANNEL_NAMES[i]
            )

        median = float(
            np.median(
                band[valid]
            )
        )

        band[
            ~valid
        ] = median

        image[
            :,
            :,
            i
        ] = band

    return image


# ============================================================
# BUILD LIVE IMAGE
# ============================================================

def build_live_landslide_image(
    latitude,
    longitude
):

    print()
    print("=" * 70)
    print(
        "BUILDING LIVE LANDSLIDE IMAGE"
    )
    print("=" * 70)

    # ========================================================
    # DATE
    # ========================================================

    start_date, end_date = (
        get_date_range()
    )

    print(
        "Date range:",
        start_date
        .format(
            "YYYY-MM-dd"
        )
        .getInfo(),
        "to",
        end_date
        .format(
            "YYYY-MM-dd"
        )
        .getInfo()
    )

    # ========================================================
    # LOCATION
    # ========================================================

    point = ee.Geometry.Point([
        float(longitude),
        float(latitude)
    ])

    region = (
        point
        .buffer(640)
        .bounds()
    )

    # ========================================================
    # SENTINEL-2
    # ========================================================

    print()
    print(
        "Searching Sentinel-2..."
    )

    s2_raw = (
        ee.ImageCollection(
            S2_COLLECTION
        )
        .filterBounds(
            point
        )
        .filterDate(
            start_date,
            end_date
        )
        .filter(
            ee.Filter.lt(
                "CLOUDY_PIXEL_PERCENTAGE",
                90
            )
        )
    )

    s2_count = (
        s2_raw
        .size()
        .getInfo()
    )

    print(
        "Sentinel-2 images found:",
        s2_count
    )

    if s2_count == 0:

        raise RuntimeError(
            "No Sentinel-2 images found."
        )

    # ========================================================
    # ACQUISITION DATE
    # ========================================================

    latest = (
        s2_raw
        .sort(
            "system:time_start",
            False
        )
        .first()
    )

    acquisition_date = (
        ee.Date(
            latest.get(
                "system:time_start"
            )
        )
        .format(
            "YYYY-MM-dd'T'HH:mm:ss"
        )
        .getInfo()
    )

    print(
        "Latest acquisition:",
        acquisition_date
    )

    # ========================================================
    # CLOUD PROBABILITY
    # ========================================================

    print()
    print(
        "Searching cloud probability..."
    )

    cloud_collection = (
        ee.ImageCollection(
            S2_CLOUD_COLLECTION
        )
        .filterBounds(
            point
        )
        .filterDate(
            start_date,
            end_date
        )
    )

    cloud_count = (
        cloud_collection
        .size()
        .getInfo()
    )

    print(
        "Cloud probability images found:",
        cloud_count
    )

    # ========================================================
    # JOIN
    # ========================================================

    join_filter = ee.Filter.equals(
        leftField="system:index",
        rightField="system:index"
    )

    joined = (
        ee.Join
        .saveFirst(
            "cloud_probability"
        )
        .apply(
            primary=s2_raw,
            secondary=cloud_collection,
            condition=join_filter
        )
    )

    joined_collection = (
        ee.ImageCollection(
            joined
        )
    )

    joined_count = (
        joined_collection
        .size()
        .getInfo()
    )

    print(
        "Joined images:",
        joined_count
    )

    # ========================================================
    # ALOS
    # ========================================================

    dem, slope = build_alos()

    # ========================================================
    # SENTINEL COMPOSITE
    # ========================================================

    raw_composite = (
        s2_raw
        .median()
    )

    if joined_count > 0:

        print()
        print(
            "Creating cloud-masked composite..."
        )

        cloud_masked = (
            joined_collection
            .map(
                apply_cloud_mask
            )
        )

        clear_composite = (
            cloud_masked
            .median()
        )

        # ----------------------------------------------------
        # VERY IMPORTANT
        #
        # Cloud masks can leave pixels masked.
        # Do NOT let sampleRectangle turn those into fake
        # reflectance = 0.
        #
        # Fill them from the raw composite.
        # ----------------------------------------------------

        s2_composite = (
            clear_composite
            .unmask(
                raw_composite
            )
        )

    else:

        print()
        print(
            "No cloud-probability matches."
        )

        print(
            "Using raw Sentinel-2 composite."
        )

        s2_composite = raw_composite

    # ========================================================
    # BUILD 14 CHANNELS
    # ========================================================

    final_image = (
        build_14_channel_stack(
            s2_composite,
            dem,
            slope
        )
    )

    # ========================================================
    # SAMPLE
    # ========================================================

    image = sample_rectangle(
        final_image,
        region
    )

    # ========================================================
    # CLEAN
    # ========================================================

    image = clean_image(
        image
    )

    # ========================================================
    # RESIZE
    # ========================================================

    print()
    print(
        "Raw GEE image shape:",
        image.shape
    )

    if image.shape[:2] != (
        128,
        128
    ):

        print(
            "Resizing to 128 x 128..."
        )

        channels = []

        for i in range(14):

            resized = cv2.resize(
                image[
                    :,
                    :,
                    i
                ],
                (
                    128,
                    128
                ),
                interpolation=cv2.INTER_LINEAR
            )

            channels.append(
                resized
            )

        image = np.stack(
            channels,
            axis=-1
        ).astype(
            np.float32
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    print()
    print("=" * 70)
    print(
        "LIVE LANDSLIDE CHANNEL DISTRIBUTION"
    )
    print("=" * 70)

    for i, name in enumerate(
        CHANNEL_NAMES
    ):

        band = image[
            :,
            :,
            i
        ]

        print(
            f"{i:2d} {name:<6} | "
            f"min={band.min():10.4f} | "
            f"max={band.max():10.4f} | "
            f"mean={band.mean():10.4f} | "
            f"std={band.std():10.4f}"
        )

    # ========================================================
    # CRITICAL CHECK
    # ========================================================

    if image[
        :,
        :,
        12
    ].std() < 1e-6:

        raise RuntimeError(
            "SLOPE CHANNEL IS STILL CONSTANT. "
            "Live prediction stopped because the "
            "topographic input is invalid."
        )

    if not np.isfinite(
        image
    ).all():

        raise RuntimeError(
            "Live image contains NaN or Inf."
        )

    if image.shape != (
        128,
        128,
        14
    ):

        raise RuntimeError(
            "Unexpected final image shape: "
            + str(image.shape)
        )

    print()
    print("=" * 70)
    print(
        "FINAL MODEL IMAGE"
    )
    print("=" * 70)

    print(
        "Shape:",
        image.shape
    )

    print(
        "Dtype:",
        image.dtype
    )

    print(
        "Range:",
        float(
            image.min()
        ),
        "to",
        float(
            image.max()
        )
    )

    print(
        "Overall std:",
        float(
            image.std()
        )
    )

    return (
        image,
        acquisition_date
    )


# ============================================================
# RUN MODEL
# ============================================================

def run_landslide_model(
    image
):

    from landslide_model import (
        predict_landslide
    )

    print()
    print("=" * 70)
    print(
        "RUNNING LANDSLIDE V5 MODEL"
    )
    print("=" * 70)

    result = predict_landslide(
        image
    )

    mask = np.asarray(
        result["mask"],
        dtype=np.uint8
    )

    probability = np.asarray(
        result["probability"],
        dtype=np.float32
    )

    coverage = float(
        result[
            "landslide_percentage"
        ]
    )

    mean_probability = float(
        probability.mean()
    )

    max_probability = float(
        probability.max()
    )

    landslide_pixels = int(
        mask.sum()
    )

    total_pixels = int(
        mask.size
    )

    # ========================================================
    # PROJECT RISK
    # ========================================================

    if coverage >= 20:

        risk = "HIGH"

    elif coverage >= 5:

        risk = "MEDIUM"

    else:

        risk = "LOW"

    print()
    print("=" * 70)
    print(
        "LANDSLIDE RESULT"
    )
    print("=" * 70)

    print(
        f"Coverage         : {coverage:.2f}%"
    )

    print(
        f"Mean probability : {mean_probability:.6f}"
    )

    print(
        f"Max probability  : {max_probability:.6f}"
    )

    print(
        f"Landslide pixels : {landslide_pixels}"
    )

    print(
        f"Total pixels     : {total_pixels}"
    )

    print(
        f"Risk             : {risk}"
    )

    return {

        "coverage":
            coverage,

        "landslide_coverage_percent":
            coverage,

        "mean_probability":
            mean_probability,

        "max_probability":
            max_probability,

        "landslide_pixels":
            landslide_pixels,

        "total_pixels":
            total_pixels,

        "risk":
            risk,

        "risk_level":
            risk,

        "mask":
            mask.tolist(),
    }


# ============================================================
# API FUNCTION
# ============================================================

def analyze_landslide(
    latitude,
    longitude
):

    try:

        image, acquisition_date = (
            build_live_landslide_image(
                latitude,
                longitude
            )
        )

        prediction = (
            run_landslide_model(
                image
            )
        )

        return {

            "success":
                True,

            "satellite":
                "Sentinel-2",

            "acquisition":
                acquisition_date,

            "acquisition_date":
                acquisition_date,

            **prediction,
        }

    except Exception as e:

        print()
        print("=" * 70)
        print(
            "LANDSLIDE PIPELINE ERROR"
        )
        print("=" * 70)

        print(
            type(e).__name__,
            ":",
            str(e)
        )

        empty_mask = np.zeros(
            (
                128,
                128
            ),
            dtype=np.uint8
        )

        return {

            "success":
                False,

            "error":
                str(e),

            "satellite":
                "Sentinel-2",

            "acquisition":
                None,

            "acquisition_date":
                None,

            "coverage":
                0.0,

            "landslide_coverage_percent":
                0.0,

            "mean_probability":
                0.0,

            "max_probability":
                0.0,

            "landslide_pixels":
                0,

            "total_pixels":
                16384,

            "risk":
                "UNKNOWN",

            "risk_level":
                "UNKNOWN",

            "mask":
                empty_mask.tolist(),
        }


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    LATITUDE = 30.7046
    LONGITUDE = 76.7179

    result = analyze_landslide(
        LATITUDE,
        LONGITUDE
    )

    print()
    print("=" * 70)
    print(
        "FINAL API RESULT"
    )
    print("=" * 70)

    print(
        "Success:",
        result.get(
            "success"
        )
    )

    print(
        "Satellite:",
        result.get(
            "satellite"
        )
    )

    print(
        "Acquisition:",
        result.get(
            "acquisition_date"
        )
    )

    print(
        "Coverage:",
        result.get(
            "landslide_coverage_percent"
        ),
        "%"
    )

    print(
        "Mean Probability:",
        result.get(
            "mean_probability"
        )
    )

    print(
        "Max Probability:",
        result.get(
            "max_probability"
        )
    )

    print(
        "Risk:",
        result.get(
            "risk_level"
        )
    )