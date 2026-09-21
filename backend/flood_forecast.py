"""
TerraWatch - Future Flood Forecast Data Layer

This module fetches real weather forecast data for a selected
latitude/longitude and prepares it for the future flood-risk
prediction layer.

Current architecture:

Location
   ↓
Open-Meteo forecast
   ↓
24h / 48h / 72h weather features
   ↓
Future flood prediction model (next step)

This file does NOT replace the existing Sentinel-1 + U-Net
flood detection pipeline.
"""

from datetime import datetime, timezone
from typing import Any

import requests


# ============================================================
# CONFIGURATION
# ============================================================

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

REQUEST_TIMEOUT = 15


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _safe_float(value: Any) -> float:
    """
    Safely convert a value to float.

    Returns 0.0 if the value is missing or cannot be converted.
    """
    try:
        if value is None:
            return 0.0

        return float(value)

    except (TypeError, ValueError):
        return 0.0


def _sum_values(values: list[Any]) -> float:
    """
    Safely sum a list of numeric values.
    """
    return sum(_safe_float(value) for value in values)


# ============================================================
# WEATHER FORECAST
# ============================================================

def get_weather_forecast(
    latitude: float,
    longitude: float,
) -> dict:
    """
    Fetch weather forecast data for a location.

    The forecast covers the next 72 hours.

    Returned information includes:
        - hourly rainfall
        - temperature
        - humidity
        - wind speed
        - rainfall totals for 24/48/72 hours

    Parameters
    ----------
    latitude : float
        Latitude of the selected location.

    longitude : float
        Longitude of the selected location.

    Returns
    -------
    dict
        Forecast information prepared for TerraWatch.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,

        # We need the next 72 hours.
        "forecast_days": 3,

        # Weather variables we currently need.
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "wind_speed_10m"
        ),

        # Use UTC internally so the backend has a consistent
        # reference for calculations.
        "timezone": "UTC",
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as exc:

        return {
            "success": False,
            "error": f"Weather forecast request failed: {exc}",
        }

    except ValueError as exc:

        return {
            "success": False,
            "error": f"Invalid weather API response: {exc}",
        }

    # --------------------------------------------------------
    # Extract hourly data
    # --------------------------------------------------------

    hourly = data.get("hourly", {})

    times = hourly.get("time", [])

    precipitation = hourly.get("precipitation", [])

    temperature = hourly.get("temperature_2m", [])

    humidity = hourly.get("relative_humidity_2m", [])

    wind_speed = hourly.get("wind_speed_10m", [])

    # --------------------------------------------------------
    # Validate response
    # --------------------------------------------------------

    if not times:

        return {
            "success": False,
            "error": "Weather API returned no hourly forecast data.",
        }

    # --------------------------------------------------------
    # Keep only the first 72 hours
    # --------------------------------------------------------

    precipitation = precipitation[:72]
    temperature = temperature[:72]
    humidity = humidity[:72]
    wind_speed = wind_speed[:72]
    times = times[:72]

    # --------------------------------------------------------
    # Calculate rainfall windows
    # --------------------------------------------------------

    rainfall_24h = _sum_values(precipitation[:24])

    rainfall_48h = _sum_values(precipitation[:48])

    rainfall_72h = _sum_values(precipitation[:72])

    # --------------------------------------------------------
    # Average weather values
    # --------------------------------------------------------

    def average(values: list[Any]) -> float:

        numeric_values = [
            _safe_float(value)
            for value in values
        ]

        if not numeric_values:
            return 0.0

        return sum(numeric_values) / len(numeric_values)

    temperature_24h = average(temperature[:24])

    humidity_24h = average(humidity[:24])

    wind_speed_24h = average(wind_speed[:24])

    # --------------------------------------------------------
    # Maximum values
    # --------------------------------------------------------

    def maximum(values: list[Any]) -> float:

        numeric_values = [
            _safe_float(value)
            for value in values
        ]

        if not numeric_values:
            return 0.0

        return max(numeric_values)

    max_rainfall_hour = maximum(precipitation[:24])

    max_wind_speed = maximum(wind_speed[:24])

    # --------------------------------------------------------
    # Create hourly forecast records
    # --------------------------------------------------------

    hourly_forecast = []

    total_hours = min(
        len(times),
        len(precipitation),
        len(temperature),
        len(humidity),
        len(wind_speed),
    )

    for i in range(total_hours):

        hourly_forecast.append(
            {
                "time": times[i],
                "precipitation_mm": round(
                    _safe_float(precipitation[i]),
                    2,
                ),
                "temperature_c": round(
                    _safe_float(temperature[i]),
                    2,
                ),
                "humidity_percent": round(
                    _safe_float(humidity[i]),
                    2,
                ),
                "wind_speed_kmh": round(
                    _safe_float(wind_speed[i]),
                    2,
                ),
            }
        )

    # --------------------------------------------------------
    # Return prepared forecast
    # --------------------------------------------------------

    return {
        "success": True,

        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },

        "source": "Open-Meteo",

        "forecast_generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "forecast_hours": total_hours,

        "rainfall": {
            "next_24h_mm": round(rainfall_24h, 2),
            "next_48h_mm": round(rainfall_48h, 2),
            "next_72h_mm": round(rainfall_72h, 2),
            "maximum_hourly_rainfall_24h_mm": round(
                max_rainfall_hour,
                2,
            ),
        },

        "weather": {
            "average_temperature_24h_c": round(
                temperature_24h,
                2,
            ),
            "average_humidity_24h_percent": round(
                humidity_24h,
                2,
            ),
            "average_wind_speed_24h_kmh": round(
                wind_speed_24h,
                2,
            ),
            "maximum_wind_speed_24h_kmh": round(
                max_wind_speed,
                2,
            ),
        },

        "hourly_forecast": hourly_forecast,
    }


# ============================================================
# SIMPLE TEST
# ============================================================

if __name__ == "__main__":

    # Chandigarh test location
    latitude = 30.7333
    longitude = 76.7794

    print("\n==========================================")
    print("       TERRAWATCH FLOOD FORECAST")
    print("==========================================")

    print(
        f"\nLocation: "
        f"{latitude}, {longitude}"
    )

    print("\nFetching 72-hour weather forecast...")

    result = get_weather_forecast(
        latitude,
        longitude,
    )

    if not result["success"]:

        print("\n❌ Forecast failed")

        print(
            result.get(
                "error",
                "Unknown error",
            )
        )

    else:

        print("\n✅ Forecast received")

        print(
            "\nRainfall forecast:"
        )

        print(
            "Next 24h:",
            result["rainfall"]["next_24h_mm"],
            "mm",
        )

        print(
            "Next 48h:",
            result["rainfall"]["next_48h_mm"],
            "mm",
        )

        print(
            "Next 72h:",
            result["rainfall"]["next_72h_mm"],
            "mm",
        )

        print(
            "\nWeather:"
        )

        print(
            "Average temperature:",
            result["weather"][
                "average_temperature_24h_c"
            ],
            "°C",
        )

        print(
            "Average humidity:",
            result["weather"][
                "average_humidity_24h_percent"
            ],
            "%",
        )

        print(
            "Average wind:",
            result["weather"][
                "average_wind_speed_24h_kmh"
            ],
            "km/h",
        )

        print(
            "\nFirst forecast hour:"
        )

        if result["hourly_forecast"]:

            print(
                result["hourly_forecast"][0]
            )

        print("\n==========================================")
        print("          FORECAST DATA READY")
        print("==========================================")