# 🌦️ SA Weather Data Pipeline

An end-to-end ELT pipeline that extracts South African weather data from the
[Open-Meteo API](https://open-meteo.com/) (free, no API key needed) across all
9 provinces and 38 cities, loads it into a PostgreSQL data warehouse through a
**Bronze → Silver → Gold** medallion architecture, orchestrated with Apache
Airflow, containerised with Docker, validated with SODA data quality checks,
and tested with pytest + GitHub Actions CI/CD.

---

## 🏗️ Architecture

```
Open-Meteo API (free, no key required)
        │
        ▼
┌─────────────────────┐
│   extract_dag       │  Airflow DAG — runs daily
│   weather_extract.py│  Fetches 38 cities × 9 provinces
└────────┬────────────┘
         │
         ▼
  weather_data_YYYY-MM-DD.json  (written to /data/)
         │
         ▼
┌─────────────────────┐
│   load_dag          │  Airflow DAG — Bronze → Silver → Gold
└────────┬────────────┘
         │
         ├──▶ BRONZE  (raw JSON, untouched)
         │    ├── raw_weather_hourly
         │    ├── raw_weather_daily
         │    └── raw_astronomy
         │
         ├──▶ SILVER  (cleaned, typed, exploded)
         │    ├── dim_cities
         │    ├── weather_hourly
         │    ├── weather_daily
         │    └── astronomy
         │
         └──▶ GOLD    (aggregated views)
              ├── daily_summary
              ├── province_summary
              ├── hottest_cities
              ├── rainiest_cities
              ├── weekly_trends
              └── city_comparison
         │
         ▼
┌─────────────────────┐
│   quality_dag       │  SODA checks between layers
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   DBeaver           │  Query + explore data visually
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  pytest + CI/CD     │  GitHub Actions — runs on every push
└─────────────────────┘
```

---

## 🛠️ Stack

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11 | Extraction + transformation logic |
| Open-Meteo API | - | Free weather data, no API key needed |
| PostgreSQL | 15 | Data warehouse |
| Apache Airflow | 2.9.1 | Pipeline orchestration |
| Docker | - | Containerisation |
| SODA | 3.3.3 | Data quality checks |
| pytest | 8.1.1 | Unit + integration testing |
| GitHub Actions | - | CI/CD automation |
| DBeaver | 26.1.0 | Database GUI |

---

## 🗺️ Coverage — 9 Provinces, 38 Cities

| Province | Cities |
|---|---|
| Gauteng | Pretoria, Johannesburg, Soweto, Ekurhuleni, Centurion, Sandton, Midrand |
| Western Cape | Cape Town, Stellenbosch, George, Paarl, Knysna, Hermanus |
| KwaZulu-Natal | Durban, Pietermaritzburg, Richards Bay, Newcastle, Ladysmith |
| Eastern Cape | Gqeberha, East London, Mthatha, Bhisho |
| Limpopo | Polokwane, Tzaneen, Thohoyandou, Bela-Bela |
| Mpumalanga | Mbombela, Witbank, Secunda |
| North West | Rustenburg, Mahikeng, Klerksdorp |
| Free State | Bloemfontein, Welkom, Phuthaditjhaba |
| Northern Cape | Kimberley, Upington, Springbok |

---

## 📁 Project Structure

```
weather-data-pipeline/
│
├── dockerfile                        # Custom Airflow image
├── docker-compose.yaml               # Postgres + Airflow containers
├── requirements.txt                  # Python dependencies
├── .env                              # Secrets — never committed
├── .env.example                      # Safe template — committed
├── .gitignore
├── README.md
│
├── dags/                             # Airflow watches this folder
│   ├── extract_dag.py                # DAG 1 — hits API, saves JSON
│   ├── load_dag.py                   # DAG 2 — JSON → bronze → silver → gold
│   ├── quality_dag.py                # DAG 3 — SODA quality checks
│   │
│   ├── api/
│   │   └── weather_extract.py        # fetch_weather(), save_to_json()
│   │
│   └── datawarehouse/
│       ├── data_loading.py           # loads JSON into bronze
│       ├── data_utils.py             # DB connection + load_sql() helper
│       ├── data_modification.py      # insert / upsert logic
│       └── data_transformation.py    # bronze → silver → gold transforms
│
├── scripts/                          # All SQL lives here — never in Python
│   ├── init_database.sql             # Creates bronze, silver, gold schemas
│   ├── bronze/
│   │   ├── ddl_bronze_hourly.sql
│   │   ├── ddl_bronze_daily.sql
│   │   └── ddl_bronze_astronomy.sql
│   ├── silver/
│   │   ├── ddl_silver_dim_cities.sql
│   │   ├── ddl_silver_weather_hourly.sql
│   │   ├── ddl_silver_weather_daily.sql
│   │   └── ddl_silver_astronomy.sql
│   └── gold/
│       ├── ddl_gold_daily_summary.sql
│       ├── ddl_gold_province_summary.sql
│       ├── ddl_gold_hottest_cities.sql
│       ├── ddl_gold_rainiest_cities.sql
│       ├── ddl_gold_weekly_trends.sql
│       └── ddl_gold_city_comparison.sql
│
├── include/
│   └── soda/
│       ├── bronze_checks.yml
│       ├── silver_checks.yml
│       └── gold_checks.yml
│
├── tests/
│   ├── unit/
│   │   ├── test_weather_extract.py
│   │   └── test_data_transformation.py
│   └── integration/
│       └── test_pipeline.py
│
├── .github/
│   └── workflows/
│       └── ci_cd.yml
│
├── data/                             # JSON drops here — git ignored
├── logs/                             # Airflow logs — git ignored
└── docs/
    ├── 01_introduction.md
    ├── 02_open_meteo_api.md
    ├── 03_docker.md
    ├── 04_airflow.md
    └── 05_postgres_and_dbeaver.md
```

---

## 🚀 Getting Started

### Prerequisites
- Docker Desktop installed and running
- Python 3.11+
- DBeaver
- Git

### 1. Clone the repo
```bash
git clone https://github.com/Morobang/weather-data-pipeline.git
cd weather-data-pipeline
```

### 2. Generate a Fernet key
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Set up your environment
```bash
cp .env.example .env
# Open .env and paste your Fernet key
```

### 4. Start the stack
```bash
docker-compose up airflow-init
docker-compose up -d
```

### 5. Verify
- Airflow UI → http://localhost:8080 (admin / admin)
- DBeaver → localhost:5432 / weather_db / rocket

### 6. Run tests
```bash
pytest tests/
```

---

## 📐 SQL-First Rule

All SQL lives in `scripts/`. Python never contains SQL strings. Every query
is loaded from a `.sql` file:

```python
def load_sql(filepath: str) -> str:
    return Path(filepath).read_text()

cursor.execute(load_sql("scripts/bronze/ddl_bronze_hourly.sql"))
```

---

## 👤 Author

**Morobang Tshigidimisa**
[GitHub](https://github.com/Morobang) ·
[Portfolio](https://morobangtshigidimisa.vercel.app) ·
[LinkedIn](https://linkedin.com/in/morobangtshigidimisa)
