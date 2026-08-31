import { useState, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  useMap,
  useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

// Default map view: India
const DEFAULT_POSITION = [22.5937, 78.9629];

/* ==========================================
   MAP CONTROLLER
   Smoothly moves the map whenever a new
   location is selected and handles map clicks.
========================================== */
function MapController({ position, onMapClick }) {
  const map = useMap();

  useEffect(() => {
    if (position) {
      map.flyTo(position, 11, {
        duration: 1.5,
      });
    }
  }, [position, map]);

  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    },
  });

  return null;
}

function App() {
  const [locationQuery, setLocationQuery] = useState("");
  const [selectedLocationName, setSelectedLocationName] = useState("");
  const [result, setResult] = useState(null);
  const [mapPosition, setMapPosition] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [error, setError] = useState("");

  /* ==========================================
     CITY SEARCH
     Convert a city/location name into coordinates
  ========================================== */
  const findLocation = async (query) => {
    const searchResponse = await fetch(
      `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(
        query
      )}`
    );

    if (!searchResponse.ok) {
      throw new Error("Could not search for this location");
    }

    const locations = await searchResponse.json();

    if (!locations || locations.length === 0) {
      throw new Error(
        "Location not found. Try a city name like Chandigarh, Delhi or New York."
      );
    }

    return {
      latitude: parseFloat(locations[0].lat),
      longitude: parseFloat(locations[0].lon),
      name: locations[0].display_name,
    };
  };

  /* ==========================================
     REVERSE GEOCODING
     Convert clicked map coordinates into a place name
  ========================================== */
  const getLocationNameFromCoordinates = async (
    latitude,
    longitude
  ) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`
      );

      if (!response.ok) {
        return `Selected Location (${latitude.toFixed(
          4
        )}, ${longitude.toFixed(4)})`;
      }

      const data = await response.json();

      if (data && data.display_name) {
        return data.display_name;
      }

      return `Selected Location (${latitude.toFixed(
        4
      )}, ${longitude.toFixed(4)})`;
    } catch {
      return `Selected Location (${latitude.toFixed(
        4
      )}, ${longitude.toFixed(4)})`;
    }
  };

  /* ==========================================
     ANALYZE COORDINATES
     Sends coordinates directly to TerraWatch API
  ========================================== */
  const analyzeCoordinates = async (
    latitude,
    longitude,
    locationName
  ) => {
    setError("");
    setResult(null);
    setLoading(true);

    // Move map immediately
    setMapPosition([latitude, longitude]);
    setSelectedLocationName(locationName);

    try {
      console.log("Starting analysis:", latitude, longitude);

      const response = await fetch(
        `${API_URL}/analyze?latitude=${latitude}&longitude=${longitude}`
      );

      console.log(
        "Analysis response status:",
        response.status
      );

      if (!response.ok) {
        throw new Error(
          `Analysis failed with status ${response.status}`
        );
      }

      const data = await response.json();

      console.log("Analysis result:", data);

      setResult(data);
      setBackendOnline(true);
    } catch (err) {
      console.error("Analysis error:", err);

      setBackendOnline(false);

      setError(
        err.message ||
          "Something went wrong while analyzing the location."
      );
    } finally {
      console.log("Analysis finished");
      setLoading(false);
    }
  };

  /* ==========================================
     SEARCH + ANALYZE
  ========================================== */
  const analyzeLocation = async () => {
    setError("");

    const query = locationQuery.trim();

    if (!query) {
      setError("Please enter a city name or coordinates.");
      return;
    }

    try {
      let latitude;
      let longitude;
      let locationName;

      // Check whether user entered coordinates
      const coordinateValues = query.split(",");

      if (coordinateValues.length === 2) {
        const possibleLatitude = parseFloat(
          coordinateValues[0].trim()
        );

        const possibleLongitude = parseFloat(
          coordinateValues[1].trim()
        );

        if (
          !isNaN(possibleLatitude) &&
          !isNaN(possibleLongitude)
        ) {
          latitude = possibleLatitude;
          longitude = possibleLongitude;

          locationName = `Selected Location (${latitude.toFixed(
            4
          )}, ${longitude.toFixed(4)})`;
        } else {
          const location = await findLocation(query);

          latitude = location.latitude;
          longitude = location.longitude;
          locationName = location.name;
        }
      } else {
        // Search city/place name
        const location = await findLocation(query);

        latitude = location.latitude;
        longitude = location.longitude;
        locationName = location.name;
      }

      await analyzeCoordinates(
        latitude,
        longitude,
        locationName
      );
    } catch (err) {
      console.error("Location search error:", err);

      setError(
        err.message ||
          "Something went wrong while finding the location."
      );
    }
  };

  /* ==========================================
     MAP CLICK
     Click anywhere → find place → analyze
  ========================================== */
  const handleMapClick = async (latitude, longitude) => {
    if (loading) return;

    setError("");

    // Move marker immediately
    setMapPosition([latitude, longitude]);

    const temporaryName = `Selected Location (${latitude.toFixed(
      4
    )}, ${longitude.toFixed(4)})`;

    setSelectedLocationName(temporaryName);
    setLocationQuery("Finding location...");

    try {
      const locationName =
        await getLocationNameFromCoordinates(
          latitude,
          longitude
        );

      setSelectedLocationName(locationName);
      setLocationQuery(locationName);

      await analyzeCoordinates(
        latitude,
        longitude,
        locationName
      );
    } catch (err) {
      console.error(err);
      setError("Could not analyze the selected map location.");
      setLoading(false);
    }
  };

  /* ==========================================
     RISK DISPLAY HELPERS
  ========================================== */
  const getRiskClass = () => {
    if (!result) return "ready";

    const level = String(
      result.alert_level || ""
    ).toUpperCase();

    if (level === "HIGH") return "high";
    if (level === "MEDIUM") return "medium";

    return "low";
  };

  const riskScore = result
    ? Number(result.weather_risk_score || 0)
    : 0;

  return (
    <div className="app">
      {/* ================= SIDEBAR ================= */}
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">🌍</div>

          <div>
            <h2>TerraWatch</h2>
            <p>AI Disaster Intelligence</p>
          </div>
        </div>

        <nav className="nav">
          <button className="nav-item active">
            ▣ Dashboard
          </button>

          <button className="nav-item">
            ⌖ Live Map
          </button>

          <button className="nav-item">
            🌊 Flood Analysis
          </button>

          <button className="nav-item">
            ⛰ Landslide
          </button>

          <button className="nav-item">
            ▥ Analytics
          </button>

          <button className="nav-item">
            ⚙ Settings
          </button>
        </nav>

        <div className="system-status">
          <span className="status-title">
            SYSTEM STATUS
          </span>

          <div className="online-row">
            <span
              className={`status-dot ${
                backendOnline ? "online" : "offline"
              }`}
            ></span>

            <strong>
              {backendOnline
                ? "TerraWatch AI Online"
                : "Backend Standby"}
            </strong>
          </div>

          <p>Satellite + AI + Weather</p>
        </div>
      </aside>

      {/* ================= MAIN CONTENT ================= */}
      <main className="main-content">
        <header className="top-header">
          <div>
            <h1>AI-Powered Disaster Intelligence</h1>
            <p>
              Satellite intelligence for a safer tomorrow
            </p>
          </div>

          <div
            className={`backend-pill ${
              backendOnline ? "connected" : ""
            }`}
          >
            🛰️{" "}
            {backendOnline
              ? "TerraWatch Backend Connected"
              : "System Ready"}

            <span
              className={
                backendOnline ? "online-dot" : ""
              }
            ></span>
          </div>
        </header>

        {/* ================= TOP GRID ================= */}
        <section className="top-grid">
          {/* ================= LIVE FLOOD CARD ================= */}
          <div className="card live-card">
            <div className="card-header">
              <div>
                <h2>Live Flood Intelligence</h2>
                <span className="live-badge">
                  ● LIVE
                </span>
              </div>

              <div className="analysis-controls">
                <input
                  type="text"
                  value={locationQuery}
                  onChange={(e) =>
                    setLocationQuery(e.target.value)
                  }
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      analyzeLocation();
                    }
                  }}
                  placeholder="Search city or enter coordinates"
                />

                <button
                  className="analyze-btn"
                  onClick={analyzeLocation}
                  disabled={loading}
                >
                  {loading
                    ? "Analyzing..."
                    : "Analyze"}
                </button>
              </div>
            </div>

            {/* ================= LIVE MAP ================= */}
            <div className="map-area">
              <div className="live-map-wrapper">
                <MapContainer
                  center={DEFAULT_POSITION}
                  zoom={5}
                  scrollWheelZoom={true}
                  className="leaflet-map"
                >
                  <TileLayer
                    attribution="Tiles &copy; Esri"
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
                  />

                  <MapController
                    position={mapPosition}
                    onMapClick={handleMapClick}
                  />

                  {mapPosition && (
                    <Marker position={mapPosition}>
                      <Popup>
                        <strong>
                          {selectedLocationName ||
                            "Selected Location"}
                        </strong>

                        {result && (
                          <>
                            <br />
                            Alert Level:{" "}
                            {result.alert_level}
                            <br />
                            Weather Risk:{" "}
                            {result.weather_risk_level}
                          </>
                        )}
                      </Popup>
                    </Marker>
                  )}
                </MapContainer>

                {!mapPosition &&
                  !loading &&
                  !error && (
                    <div className="map-welcome-message">
                      <span>🛰️</span>

                      <div>
                        <strong>
                          TerraWatch Live Intelligence
                        </strong>

                        <p>
                          Search for a city or click anywhere
                          on the map
                        </p>
                      </div>
                    </div>
                  )}

                {loading && (
                  <div className="map-loading-overlay">
                    <div className="scanner">◌</div>

                    <p>
                      Finding location and analyzing data...
                    </p>
                  </div>
                )}

                {error && (
                  <div className="map-error-overlay">
                    ⚠️ {error}
                  </div>
                )}

                {result && !loading && (
                  <div className="map-result-overlay">
                    <div
                      className={`result-icon ${getRiskClass()}`}
                    >
                      🌊
                    </div>

                    <div className="result-info">
                      <span
                        className={`alert-label ${getRiskClass()}`}
                      >
                        {result.alert_level} RISK
                      </span>

                      <h2>
                        {result.overall_status}
                      </h2>

                      <div className="location-display">
                        📍{" "}
                        {selectedLocationName ||
                          `${result.location?.latitude || ""}, ${
                            result.location?.longitude || ""
                          }`}
                      </div>

                      <div className="map-overlay-details">
                        <span>
                          🛰️ {result.satellite_status}
                        </span>

                        <span>
                          🌦️{" "}
                          {result.weather_risk_level}{" "}
                          Weather Risk
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ================= RISK OVERVIEW ================= */}
          <div className="card risk-card">
            <h2>Flood Risk Overview</h2>

            <div
              className={`risk-gauge ${getRiskClass()}`}
            >
              <div className="gauge-inner">
                <strong>
                  {result
                    ? result.alert_level
                    : "READY"}
                </strong>

                <span>
                  {result
                    ? "Alert Level"
                    : "System Status"}
                </span>
              </div>
            </div>

            <div className="status-list">
              <div className="status-row">
                <span>AI Model</span>

                <strong className="ready-text">
                  Ready
                </strong>
              </div>

              <div className="status-row">
                <span>Satellite</span>

                <strong
                  className={
                    result ? "connected-text" : ""
                  }
                >
                  {result
                    ? "Analyzed"
                    : "Connected"}
                </strong>
              </div>

              <div className="status-row">
                <span>Weather API</span>

                <strong className="connected-text">
                  {result
                    ? result.weather_risk_level
                    : "Connected"}
                </strong>
              </div>
            </div>
          </div>
        </section>

        {/* ================= BOTTOM CARDS ================= */}
        <section className="bottom-grid">
          {/* Flood Prediction */}
          <div className="card mini-card">
            <h2>Flood Prediction</h2>

            <div className="mini-content">
              <div className="mini-icon">📈</div>

              {result ? (
                <>
                  <h3>
                    {result.alert_level} ALERT
                  </h3>

                  <p>{result.overall_status}</p>
                </>
              ) : (
                <p>
                  Prediction analytics will appear here
                </p>
              )}
            </div>
          </div>

          {/* AI Flood Probability */}
          <div className="card mini-card">
            <h2>AI Flood Probability</h2>

            <div className="probability-content">
              {result ? (
                <>
                  <div className="percentage">
                    {riskScore}%
                  </div>

                  <div className="progress-bar">
                    <div
                      className={`progress-fill ${getRiskClass()}`}
                      style={{
                        width: `${Math.min(
                          Math.max(riskScore, 0),
                          100
                        )}%`,
                      }}
                    ></div>
                  </div>

                  <p>
                    Weather-based flood risk probability
                  </p>
                </>
              ) : (
                <>
                  <div className="mini-icon">
                    🧠
                  </div>

                  <p>Model probability map</p>
                </>
              )}
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="card mini-card">
            <h2>Recent Alerts</h2>

            <div className="alerts-content">
              {result ? (
                <div
                  className={`alert-box ${getRiskClass()}`}
                >
                  <span>⚠</span>

                  <div>
                    <strong>
                      {result.alert_level} FLOOD RISK
                    </strong>

                    <p>
                      {result.overall_status}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="no-alerts">
                  <span>✓</span>

                  <p>No active alerts yet</p>

                  <small>
                    Analyze a location to get started
                  </small>
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;