from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

# Initialize the FastAPI application
app = FastAPI(title="Weather API Service")

# ---------------- CORS Setup ----------------
# This allows my API to be called from any frontend (different domains/ports).
# Without CORS, browsers would block requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all domains
    allow_credentials=True,
    allow_methods=["*"],        # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],        # Allow all headers
)

# ---------------- Config ----------------
API_KEY = "656e1f130905b7d02a64652305a9c78c"
BASE_URL = "https://api.openweathermap.org/data/2.5"

# In-memory search history (resets when server restarts)
search_history = []

# ---------------- Rate Limiting ----------------
# Store last request times per (client_ip, query)
rate_limit_weather = {}
rate_limit_forecast = {}

def check_rate_limit_weather(client_ip, city):
    """
    Enforce weather rate limiting.
    Allows different cities within 5 minutes, but blocks repeated requests
    for the same city by the same IP.
    """
    current_time = time.time()
    key = (client_ip, city.lower())
    if key in rate_limit_weather and current_time - rate_limit_weather[key] < 300:
        raise HTTPException(
            status_code=429,
            detail=f"Too many weather requests for {city}. Please wait 5 minutes."
        )
    rate_limit_weather[key] = current_time


def check_rate_limit_forecast(client_ip, city):
    """
    Enforce forecast rate limiting.
    First request for a city is allowed immediately,
    but repeated requests for the same city are blocked within 5 minutes.
    """
    current_time = time.time()
    key = (client_ip, city.lower())
    if key not in rate_limit_forecast:
        rate_limit_forecast[key] = current_time
        return
    if current_time - rate_limit_forecast[key] < 300:  # 5 minutes
        raise HTTPException(
            status_code=429,
            detail=f"Too many forecast requests for {city}. Please wait 5 minutes."
        )
    rate_limit_forecast[key] = current_time

# ---------------- Endpoints ----------------

@app.get("/weather")
def get_weather(city: str = None, lat: float = None, lon: float = None, request: Request = None):
    """
    Get current weather by city OR coordinates.
    """
    if not city and (lat is None or lon is None):
        raise HTTPException(status_code=400, detail="City or coordinates required")
    
    # Query key is city name if provided, otherwise coordinates
    query_key = city if city else f"{lat},{lon}"
    check_rate_limit_weather(request.client.host, query_key)

    # Construct the external API URL
    if city:
        url = f"{BASE_URL}/weather?q={city}&appid={API_KEY}&units=metric"
    else:
        url = f"{BASE_URL}/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"

    # Call OpenWeatherMap
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())

    data = response.json()
    # Save to history
    search_history.append({"query": query_key, "timestamp": time.ctime(), "type": "current"})
    return data


@app.get("/weather/forecast")
def get_forecast(city: str = None, lat: float = None, lon: float = None, days: int = 5, request: Request = None):
    """
    Get weather forecast by city OR coordinates for 1–5 days.
    """
    if not city and (lat is None or lon is None):
        raise HTTPException(status_code=400, detail="City or coordinates required")
    if not (1 <= days <= 5):
        raise HTTPException(status_code=400, detail="Days must be between 1 and 5")
    
    # Query key is city name if provided, otherwise coordinates
    query_key = city if city else f"{lat},{lon}"
    check_rate_limit_forecast(request.client.host, query_key)

    # Construct the external API URL
    if city:
        url = f"{BASE_URL}/forecast?q={city}&cnt={days*8}&appid={API_KEY}&units=metric"
    else:
        url = f"{BASE_URL}/forecast?lat={lat}&lon={lon}&cnt={days*8}&appid={API_KEY}&units=metric"

    
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    
    data = response.json()
    # Save to history
    search_history.append({"query": query_key, "timestamp": time.ctime(), "type": "forecast"})
    return data


@app.get("/weather/history")
def get_history():
    """Return the full search history (in memory)."""
    return search_history


@app.delete("/weather/history")
def clear_history():
    """Clear the search history."""
    search_history.clear()
    return {"detail": "History cleared"}




# ---------------- Frontend ----------------
@app.get("/", response_class=HTMLResponse)
def frontend():
    """
    Serve a simple HTML frontend that allows:
      - City search for weather
      - Forecast view
      - Viewing and clearing search history
    """
    return """
    <html>
      <head>
        <title>Weather API</title>
        <style>
          body { font-family: Arial, sans-serif; background: #f4f8fb; color: #333; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
          .container { max-width: 700px; width: 100%; text-align: center; }
          h2 { color: #2c3e50; }
          form, .controls { margin-bottom: 20px; }
          input, button { padding: 10px; font-size: 16px; border-radius: 6px; border: 1px solid #ccc; }
          button { background-color: #3498db; color: white; cursor: pointer; }
          button:hover { background-color: #2980b9; }
          .card { background: white; padding: 20px; margin: 10px 0; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); text-align: left; }
          pre { white-space: pre-wrap; word-wrap: break-word; }
          .forecast-day { margin: 10px 0; padding: 10px; border-left: 4px solid #3498db; background: #ecf6fc; border-radius: 6px; }
        </style>
      </head>
      <body>
        <div class="container">
          <h2>🌤 Weather Search</h2>
          <form id="form">
            <input type="text" id="city" placeholder="Enter city" required />
            <button type="submit">Search</button>
          </form>

          <div class="controls">
            <button onclick="loadForecast()">Show Forecast</button>
            <button onclick="clearAll()">Clear History</button>
          </div>

          <div class="card">
            <h3>Current Weather</h3>
            <div id="result">No data yet.</div>
          </div>

          <div class="card">
            <h3>Forecast</h3>
            <div id="forecast">No forecast yet.</div>
          </div>

          <div class="card">
            <h3>Search History</h3>
            <div id="history">Loading...</div>
          </div>
        </div>

        <script>
          const form = document.getElementById('form');
          form.onsubmit = async (e) => {
            e.preventDefault();
            const city = document.getElementById('city').value;
            const res = await fetch(`/weather?city=${city}`);
            const data = await res.json();
            if (data.main) {
              const ts = new Date().toLocaleString();
              document.getElementById('result').innerHTML = `
                <p><b>City:</b> ${data.name}</p>
                <p><b>Temperature:</b> ${data.main.temp} °C</p>
                <p><b>Condition:</b> ${data.weather[0].description}</p>
                <p><i>Fetched at: ${ts}</i></p>
              `;
            } else {
              document.getElementById('result').innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            }
            loadHistory();
          };

          async function loadForecast() {
            const city = document.getElementById('city').value;
            if (!city) { alert('Enter a city first!'); return; }
            const res = await fetch(`/weather/forecast?city=${city}&days=5`);
            const data = await res.json();
            if (data.list) {
              let html = '';
              const step = 8; // 8 entries per day (3h intervals)
              for (let i = 0; i < data.list.length; i += step) {
                const item = data.list[i];
                const date = new Date(item.dt * 1000);
                html += `
                  <div class="forecast-day">
                    <p><b>${date.toDateString()}</b></p>
                    <p>🌡 Temp: ${item.main.temp} °C</p>
                    <p>☁ Condition: ${item.weather[0].description}</p>
                    <p><i>Fetched at: ${new Date().toLocaleString()}</i></p>
                  </div>
                `;
              }
              document.getElementById('forecast').innerHTML = html;
            } else {
              document.getElementById('forecast').innerHTML = `<pre>${JSON.stringify(data, null, 5)}</pre>`;
            }
            loadHistory();
          }

          async function loadHistory() {
            const res = await fetch('/weather/history');
            const data = await res.json();
            let html = '';
            data.forEach(h => {
              html += `<p>${h.timestamp}: <b>${h.query}</b> (${h.type})</p>`;
            });
            document.getElementById('history').innerHTML = html || 'No history yet.';
          }

          async function clearAll() {
            await fetch('/weather/history', { method: 'DELETE' });
            document.getElementById('result').innerHTML = 'No data yet.';
            document.getElementById('forecast').innerHTML = 'No forecast yet.';
            document.getElementById('history').innerHTML = 'No history yet.';
          }

          loadHistory();
        </script>
      </body>
    </html>
    """
