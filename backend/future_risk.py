"""
TerraWatch - Future Flood Risk Engine

Combines:
1. Current Sentinel-1 + Flood V3 U-Net result
2. 72-hour Open-Meteo weather forecast
3. Baseline future flood-risk calculation

IMPORTANT:
This is currently a baseline early-warning system.
It is not yet a separately trained future-flood ML model.
"""

from flood_pipeline import analyze_flood
from flood_forecast import get_weather_forecast


# ============================================================
# HELPERS
# ============================================================

def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(maximum, float(value)))


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# RAINFALL SCORE
# ============================================================

def rainfall_score(rainfall_mm):
    """
    Convert accumulated forecast rainfall into a 0-100
    supporting risk score.

    Baseline thresholds:
        <= 5 mm   -> very low
        100+ mm   -> maximum

    These thresholds can later be calibrated using
    historical flood data.
    """

    rainfall_mm = safe_float(rainfall_mm)

    if rainfall_mm <= 5:
        return 0.0

    if rainfall_mm >= 100:
        return 100.0

    return clamp(
        ((rainfall_mm - 5) / 95) * 100
    )


# ============================================================
# HUMIDITY SCORE
# ============================================================

def humidity_score(humidity):
    """
    Humidity is a supporting weather feature.
    It should not dominate flood prediction.
    """

    humidity = safe_float(humidity)

    if humidity <= 60:
        return 0.0

    if humidity >= 95:
        return 100.0

    return clamp(
        ((humidity - 60) / 35) * 100
    )


# ============================================================
# TEMPERATURE SCORE
# ============================================================

def temperature_score(temperature):
    """
    Temperature is treated as a weak supporting feature.
    """

    temperature = safe_float(temperature)

    if temperature <= 15:
        return 0.0

    if temperature >= 35:
        return 100.0

    return clamp(
        ((temperature - 15) / 20) * 100
    )


# ============================================================
# CURRENT FLOOD SIGNAL
# ============================================================

def current_flood_score(
    flood_coverage_percentage,
    model_confidence
):
    """
    Convert current U-Net result into a 0-100 signal.
    """

    flood_coverage = clamp(
        flood_coverage_percentage
    )

    model_confidence = clamp(
        model_confidence
    )

    return clamp(
        flood_coverage * 0.70
        +
        model_confidence * 0.30
    )


# ============================================================
# RISK LEVEL
# ============================================================

def risk_level(score):

    score = safe_float(score)

    if score < 30:
        return "LOW"

    elif score < 60:
        return "MEDIUM"

    else:
        return "HIGH"


# ============================================================
# FUTURE RISK CALCULATION
# ============================================================

def calculate_future_risk(
    flood_coverage_percentage,
    model_confidence,
    rainfall_24h,
    rainfall_48h,
    rainfall_72h,
    humidity,
    temperature,
    wind_speed
):
    """
    Calculate 24h, 48h and 72h future flood risk.
    """

    # --------------------------------------------------------
    # Current satellite/U-Net signal
    # --------------------------------------------------------

    current_signal = current_flood_score(
        flood_coverage_percentage,
        model_confidence
    )

    # --------------------------------------------------------
    # Rainfall signals
    # --------------------------------------------------------

    rain_24 = rainfall_score(
        rainfall_24h
    )

    rain_48 = rainfall_score(
        rainfall_48h
    )

    rain_72 = rainfall_score(
        rainfall_72h
    )

    # --------------------------------------------------------
    # Weather supporting signals
    # --------------------------------------------------------

    humidity_signal = humidity_score(
        humidity
    )

    temperature_signal = temperature_score(
        temperature
    )

    weather_support = (
        humidity_signal * 0.70
        +
        temperature_signal * 0.30
    )

    # --------------------------------------------------------
    # 24-HOUR RISK
    # --------------------------------------------------------

    risk_24 = (
        current_signal * 0.65
        +
        rain_24 * 0.30
        +
        weather_support * 0.05
    )

    # --------------------------------------------------------
    # 48-HOUR RISK
    # --------------------------------------------------------

    risk_48 = (
        current_signal * 0.50
        +
        rain_48 * 0.45
        +
        weather_support * 0.05
    )

    # --------------------------------------------------------
    # 72-HOUR RISK
    # --------------------------------------------------------

    risk_72 = (
        current_signal * 0.40
        +
        rain_72 * 0.55
        +
        weather_support * 0.05
    )

    risk_24 = clamp(risk_24)
    risk_48 = clamp(risk_48)
    risk_72 = clamp(risk_72)

    return {
        "24h": {
            "score": round(risk_24, 2),
            "level": risk_level(risk_24)
        },

        "48h": {
            "score": round(risk_48, 2),
            "level": risk_level(risk_48)
        },

        "72h": {
            "score": round(risk_72, 2),
            "level": risk_level(risk_72)
        }
    }


# ============================================================
# COMPLETE FUTURE FLOOD ANALYSIS
# ============================================================

def analyze_future_flood(
    latitude,
    longitude
):

    print("\n==========================================")
    print("     TERRAWATCH FUTURE FLOOD ANALYSIS")
    print("==========================================")

    print(
        f"\nLocation: {latitude}, {longitude}"
    )

    # ========================================================
    # 1. CURRENT FLOOD ANALYSIS
    # ========================================================

    print(
        "\n[1/2] Running current flood analysis..."
    )

    try:

        flood_result = analyze_flood(
            latitude,
            longitude
        )

    except Exception as error:

        print(
            "\nERROR: Current flood analysis failed."
        )

        print(error)

        return {
            "success": False,
            "error": str(error)
        }

    if not flood_result.get("success", True):

        return {
            "success": False,
            "error": flood_result.get(
                "error",
                "Current flood analysis failed."
            )
        }

    # --------------------------------------------------------
    # Current flood values
    # --------------------------------------------------------

    flood_coverage = safe_float(
        flood_result.get(
            "flood_coverage_percentage",
            0
        )
    )

    model_confidence = safe_float(
        flood_result.get(
            "model_confidence",
            0
        )
    )

    current_alert = flood_result.get(
        "alert_level",
        "LOW"
    )

    satellite_date = flood_result.get(
        "satellite_image_date",
        None
    )

    print(
        f"\nCurrent flood coverage: {flood_coverage:.2f}%"
    )

    print(
        f"Current model confidence: {model_confidence:.2f}%"
    )

    print(
        f"Current alert: {current_alert}"
    )

    # ========================================================
    # 2. WEATHER FORECAST
    # ========================================================

    print(
        "\n[2/2] Getting 72-hour weather forecast..."
    )

    try:

        weather_result = get_weather_forecast(
            latitude,
            longitude
        )

    except Exception as error:

        print(
            "\nERROR: Weather forecast failed."
        )

        print(error)

        return {
            "success": False,
            "error": str(error)
        }

    if not weather_result.get("success"):

        return {
            "success": False,
            "error": weather_result.get(
                "error",
                "Weather forecast failed."
            )
        }

    # ========================================================
    # EXACT WEATHER STRUCTURE FROM YOUR FORECAST FUNCTION
    # ========================================================

    rainfall = weather_result.get(
        "rainfall",
        {}
    )

    weather = weather_result.get(
        "weather",
        {}
    )

    # --------------------------------------------------------
    # Rainfall
    # --------------------------------------------------------

    rainfall_24h = safe_float(
        rainfall.get(
            "next_24h_mm",
            0
        )
    )

    rainfall_48h = safe_float(
        rainfall.get(
            "next_48h_mm",
            0
        )
    )

    rainfall_72h = safe_float(
        rainfall.get(
            "next_72h_mm",
            0
        )
    )

    # --------------------------------------------------------
    # Weather
    #
    # These are the ACTUAL keys from your output:
    #
    # average_temperature_24h_c
    # average_humidity_24h_percent
    # average_wind_speed_24h_kmh
    # --------------------------------------------------------

    temperature = safe_float(
        weather.get(
            "average_temperature_24h_c",
            0
        )
    )

    humidity = safe_float(
        weather.get(
            "average_humidity_24h_percent",
            0
        )
    )

    wind_speed = safe_float(
        weather.get(
            "average_wind_speed_24h_kmh",
            0
        )
    )

    maximum_wind_speed = safe_float(
        weather.get(
            "maximum_wind_speed_24h_kmh",
            0
        )
    )

    # ========================================================
    # DISPLAY WEATHER
    # ========================================================

    print("\nForecast rainfall:")

    print(
        f"Next 24h: {rainfall_24h} mm"
    )

    print(
        f"Next 48h: {rainfall_48h} mm"
    )

    print(
        f"Next 72h: {rainfall_72h} mm"
    )

    print("\nWeather:")

    print(
        f"Average temperature: {temperature} °C"
    )

    print(
        f"Average humidity: {humidity} %"
    )

    print(
        f"Average wind: {wind_speed} km/h"
    )

    print(
        f"Maximum wind: {maximum_wind_speed} km/h"
    )

    # ========================================================
    # CALCULATE FUTURE RISK
    # ========================================================

    print(
        "\nCalculating future flood risk..."
    )

    future_risk = calculate_future_risk(

        flood_coverage_percentage=flood_coverage,

        model_confidence=model_confidence,

        rainfall_24h=rainfall_24h,

        rainfall_48h=rainfall_48h,

        rainfall_72h=rainfall_72h,

        humidity=humidity,

        temperature=temperature,

        wind_speed=wind_speed
    )

    # ========================================================
    # DISPLAY RISK
    # ========================================================

    print(
        "\n=========================================="
    )

    print(
        f"24-HOUR RISK: "
        f"{future_risk['24h']['level']} "
        f"({future_risk['24h']['score']:.2f})"
    )

    print(
        f"48-HOUR RISK: "
        f"{future_risk['48h']['level']} "
        f"({future_risk['48h']['score']:.2f})"
    )

    print(
        f"72-HOUR RISK: "
        f"{future_risk['72h']['level']} "
        f"({future_risk['72h']['score']:.2f})"
    )

    print(
        "=========================================="
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {

        "success": True,

        "location": {
            "latitude": latitude,
            "longitude": longitude
        },

        "current_condition": {

            "flood_coverage_percentage": round(
                flood_coverage,
                2
            ),

            "model_confidence": round(
                model_confidence,
                2
            ),

            "alert_level": current_alert,

            "satellite_image_date": satellite_date,

            # Pass the real Flood V3 pixel mask through the
            # future-risk wrapper so the Streamlit frontend can
            # render the actual segmentation instead of a circle.
            "flood_mask": flood_result.get("flood_mask", []),
            "flood_bounds": flood_result.get("flood_bounds")
        },

        "forecast_weather": {

            "next_24h_rainfall_mm": rainfall_24h,

            "next_48h_rainfall_mm": rainfall_48h,

            "next_72h_rainfall_mm": rainfall_72h,

            "average_temperature_24h_c": temperature,

            "average_humidity_24h_percent": humidity,

            "average_wind_speed_24h_kmh": wind_speed,

            "maximum_wind_speed_24h_kmh": maximum_wind_speed
        },

        "future_flood_risk": future_risk,

        "prediction_type": "baseline_early_warning"
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    LATITUDE = 26.7288
    LONGITUDE = 85.9263

    result = analyze_future_flood(
        LATITUDE,
        LONGITUDE
    )

    print("\n\nFINAL RESULT:")

    print(result)