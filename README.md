# Weather Service
A simple weather API service built with **FastAPI** that integrates with OpenWeatherMap, stores search history, includes rate limiting, and serves a basic HTML frontend.

## Features
- Current weather by **city** or **coordinates**
- 1–5 day **forecast** by city
- **Search history** stored with timestamps
- Ability to **clear history**
- **Rate limiting** (1 request every 5 minutes per IP)
- Simple **HTML frontend** for testing

## Requirements
- Python 3.9+
- OpenWeatherMap API key

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/ConfordHO/weather.git
   cd weather
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux / Mac
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```bash
   pip install fastapi uvicorn requests
   ```
4. Create a `.env` file and add your OpenWeatherMap API key:
   ```env
   API_KEY=your_openweathermap_api_key
   ```
5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```
6. Open in browser:
   ```
   http://127.0.0.1:8000
   ```
---
## API Endpoints
### 1. Current Weather by City
```http
GET /weather?city={city}
```
### 2. Current Weather by Coordinates
```http
GET /weather?lat={lat}&lon={lon}
```

### 3. Forecast by City
```http
GET /weather/forecast?city={city}&days={days}
```
- `days`: 1 to 5

### 4. Search History
```http
GET /weather/history
```
### 5. Clear History
```http
DELETE /weather/history
```

---

## Frontend
- Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in a browser
- Enter a city name to fetch current weather
- View forecast results
- View search history
- Clear history with one click
---
## Project Structure
```
.
├── main.py           # FastAPI application
├── README.md         # Setup + Documentation
├── requirements.txt  # Dependencies
├── API Documentation # Explains the entire API
└── .env              # Environment variables (API key)
```

---

## Notes
- Rate limit: 1 request per 2 seconds per IP.
- Uses OpenWeatherMap free API tier.
- History stored in-memory (resets when app restarts).

Got it — let’s create a **very elaborate environment configuration** so your project is well-structured, portable, and production-ready. I’ll cover: `.env` setup, `requirements.txt`, recommended folder layout, and environment variables for different stages (development, staging, production).

---
# Environment Configuration for Weather API Service
## 1. Project Structure
Here’s the folder layout:

```
weather-api-service/
├── main.py                  # Backend and frontend
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── README.md                # Documentation
```
---

## 2. Environment Variables (`.env`)
All sensitive or configurable values should live inside a `.env` file. This file is **never** committed to GitHub.
Example `.env`:
```env
# Server configuration
APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=True

# API Configuration
API_KEY=your_openweathermap_api_key
BASE_URL=https://api.openweathermap.org/data/2.5

# Rate limiting (seconds)
WEATHER_RATE_LIMIT=300   # 5 minutes
FORECAST_RATE_LIMIT=300  # 5 minutes

# Allowed origins for CORS
CORS_ALLOW_ORIGINS=*

# Environment type
ENV=development
```

---
## 3. Example `.env.example`
This should be committed to GitHub as a reference for new developers:

```env
APP_HOST=127.0.0.1
APP_PORT=8000
DEBUG=True

API_KEY=your_api_key_here
BASE_URL=https://api.openweathermap.org/data/2.5

WEATHER_RATE_LIMIT=300
FORECAST_RATE_LIMIT=300

CORS_ALLOW_ORIGINS=*

ENV=development
```

---

## 4. Loading Environment Variables

Use **python-dotenv** to load `.env` into your FastAPI app.
```python
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Access environment variables
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.openweathermap.org/data/2.5")
APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

---
## 5. requirements.txt

Minimal dependencies:

```
fastapi
uvicorn
requests
python-dotenv
```

For development (optional extra tools):

```
black           # code formatter
flake8          # linting
pytest          # testing
httpx           # test requests
```

---

## 6. Running the Application

### Development Mode

Run with auto-reload:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Production Mode

Use `gunicorn` with `uvicorn` workers:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 7. Environment Types
Define `ENV` in `.env`:

* **development** → debug mode enabled, reload on changes.
* **staging** → testing environment, stricter CORS.
* **production** → debug disabled, optimized for speed.

Example switch in code:
```python
ENV = os.getenv("ENV", "development")

if ENV == "production":
    DEBUG = False
else:
    DEBUG = True
```
---
## 8. 🔒 Security Notes
* Never hardcode the API key in your code.
* Add `.env` to `.gitignore`:
  ```
  # Ignore environment files
  .env
  ```
* Use different `.env` files for different environments (`.env.dev`, `.env.prod`).
