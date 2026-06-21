import requests
import json
import os
from datetime import datetime
from pathlib import Path

CITIES = [
    # Gauteng
    {"name": "Pretoria",          "province": "Gauteng",        "lat": -25.7479, "lon": 28.2293},
    {"name": "Johannesburg",      "province": "Gauteng",        "lat": -26.2041, "lon": 28.0473},
    {"name": "Soweto",            "province": "Gauteng",        "lat": -26.2677, "lon": 27.8585},
    {"name": "Ekurhuleni",        "province": "Gauteng",        "lat": -26.3592, "lon": 28.1456},
    {"name": "Centurion",         "province": "Gauteng",        "lat": -25.8601, "lon": 28.1881},
    {"name": "Sandton",           "province": "Gauteng",        "lat": -26.1070, "lon": 28.0567},
    {"name": "Midrand",           "province": "Gauteng",        "lat": -25.9981, "lon": 28.1284},

    # Western Cape
    {"name": "Cape Town",         "province": "Western Cape",   "lat": -33.9249, "lon": 18.4241},
    {"name": "Stellenbosch",      "province": "Western Cape",   "lat": -33.9321, "lon": 18.8602},
    {"name": "George",            "province": "Western Cape",   "lat": -33.9646, "lon": 22.4617},
    {"name": "Paarl",             "province": "Western Cape",   "lat": -33.7249, "lon": 18.9560},
    {"name": "Knysna",            "province": "Western Cape",   "lat": -34.0357, "lon": 23.0487},
    {"name": "Hermanus",          "province": "Western Cape",   "lat": -34.4187, "lon": 19.2345},

    # KwaZulu-Natal
    {"name": "Durban",            "province": "KwaZulu-Natal",  "lat": -29.8587, "lon": 31.0218},
    {"name": "Pietermaritzburg",  "province": "KwaZulu-Natal",  "lat": -29.6006, "lon": 30.3794},
    {"name": "Richards Bay",      "province": "KwaZulu-Natal",  "lat": -28.7831, "lon": 32.0382},
    {"name": "Newcastle",         "province": "KwaZulu-Natal",  "lat": -27.7559, "lon": 29.9318},
    {"name": "Ladysmith",         "province": "KwaZulu-Natal",  "lat": -28.5595, "lon": 29.7814},

    # Eastern Cape
    {"name": "Gqeberha",          "province": "Eastern Cape",   "lat": -33.9608, "lon": 25.6022},
    {"name": "East London",       "province": "Eastern Cape",   "lat": -33.0153, "lon": 27.9116},
    {"name": "Mthatha",           "province": "Eastern Cape",   "lat": -31.5887, "lon": 28.7840},
    {"name": "Bhisho",            "province": "Eastern Cape",   "lat": -32.8470, "lon": 27.4390},

    # Limpopo
    {"name": "Polokwane",         "province": "Limpopo",        "lat": -23.9045, "lon": 29.4689},
    {"name": "Tzaneen",           "province": "Limpopo",        "lat": -23.8305, "lon": 30.1644},
    {"name": "Thohoyandou",       "province": "Limpopo",        "lat": -22.9561, "lon": 30.4794},
    {"name": "Bela-Bela",         "province": "Limpopo",        "lat": -24.8833, "lon": 28.2833},

    # Mpumalanga
    {"name": "Mbombela",          "province": "Mpumalanga",     "lat": -25.4653, "lon": 30.9856},
    {"name": "Witbank",           "province": "Mpumalanga",     "lat": -25.8744, "lon": 29.2403},
    {"name": "Secunda",           "province": "Mpumalanga",     "lat": -26.5608, "lon": 29.2003},

    # North West
    {"name": "Rustenburg",        "province": "North West",     "lat": -25.6672, "lon": 27.2423},
    {"name": "Mahikeng",          "province": "North West",     "lat": -25.8503, "lon": 25.6442},
    {"name": "Klerksdorp",        "province": "North West",     "lat": -26.8676, "lon": 26.6517},

    # Free State
    {"name": "Bloemfontein",      "province": "Free State",     "lat": -29.0852, "lon": 26.1596},
    {"name": "Welkom",            "province": "Free State",     "lat": -27.9833, "lon": 26.7333},
    {"name": "Phuthaditjhaba",    "province": "Free State",     "lat": -28.5333, "lon": 28.8833},

    # Northern Cape
    {"name": "Kimberley",         "province": "Northern Cape",  "lat": -28.7282, "lon": 24.7499},
    {"name": "Upington",          "province": "Northern Cape",  "lat": -28.4478, "lon": 21.2561},
    {"name": "Springbok",         "province": "Northern Cape",  "lat": -29.6639, "lon": 17.8864},
]


def fetch_weather(city: dict) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":  city["lat"],
        "longitude": city["lon"],
        "hourly": [
            "temperature_2m",
            "precipitation",
            "windspeed_10m",
            "relativehumidity_2m",
        ],
        "timezone":       "Africa/Johannesburg",
        "forecast_days":  1,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return {
        "city":     city["name"],
        "province": city["province"],
        "fetched_at": datetime.now().isoformat(),
        "data":     response.json(),
    }


def save_to_json(records: list) -> str:
    output_dir = Path("/opt/airflow/data")
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"weather_data_{datetime.now().strftime('%Y-%m-%d')}.json"
    filepath = output_dir / filename
    with open(filepath, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Saved {len(records)} city records to {filepath}")
    return str(filepath)


def extract_all_cities() -> str:
    records = []
    for city in CITIES:
        print(f"Fetching {city['name']} ({city['province']})...")
        record = fetch_weather(city)
        records.append(record)
        print(f"  Done — {len(record['data']['hourly']['time'])} hourly readings")
    return save_to_json(records)


if __name__ == "__main__":
    path = extract_all_cities()
    print(f"\nOutput: {path}")
