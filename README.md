# weather-data-pipeline

An end-to-end ELT pipeline extracting South African weather data via the Open-Meteo API (free, no key needed), loading it into a PostgreSQL data warehouse through Bronze → Silver → Gold layers, orchestrated with Apache Airflow, containerised with Docker, validated with SODA data quality checks, and tested with pytest + GitHub Actions CI/CD.

## Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Extraction scripts, ELT logic |
| Open-Meteo API | Data source (free, no API key) |
| PostgreSQL | Data warehouse |
| Apache Airflow | Pipeline orchestration |
| Docker | Containerisation |
| SODA | Data quality checks |
| pytest | Unit, integration & E2E testing |
| GitHub Actions | CI/CD automation |

## Architecture

```
Open-Meteo API (free, no key)
        ↓
extract_dag  →  weather_data_YYYY-MM-DD.json  →  /data/
        ↓
load_dag
   ├── bronze schema  (raw JSON, untouched)
   ├── silver schema  (cleaned, typed)        ← SODA checks
   └── gold schema    (aggregated views)      ← SODA checks
        ↓
DBeaver  ←  query gold.daily_summary
        ↓
pytest + GitHub Actions CI/CD
```

## Cities tracked

| City | Lat | Lon |
|---|---|---|
| Pretoria | -25.7479 | 28.2293 |
| Johannesburg | -26.2041 | 28.0473 |
| Cape Town | -33.9249 | 18.4241 |
| Durban | -29.8587 | 31.0218 |

## Project structure

```
weather-data-pipeline/
├── dockerfile
├── docker-compose.yaml
├── requirements.txt
├── .env                          # never committed
├── .env.example
├── .gitignore
├── README.md
├── docker/
│   └── postgres/
│       └── init-multiple-databases.sh
├── scripts/                      # all SQL lives here
│   ├── init_database.sql
│   ├── bronze/
│   │   └── ddl_bronze.sql
│   ├── silver/
│   │   └── ddl_silver.sql
│   └── gold/
│       └── ddl_gold.sql
├── dags/
│   ├── extract_dag.py
│   ├── load_dag.py
│   ├── quality_dag.py
│   ├── api/
│   │   └── weather_extract.py
│   └── datawarehouse/
│       ├── data_loading.py
│       ├── data_utils.py
│       ├── data_modification.py
│       └── data_transformation.py
├── include/
│   └── soda/
│       ├── bronze_checks.yml
│       ├── silver_checks.yml
│       └── gold_checks.yml
├── tests/
│   ├── unit/
│   └── integration/
├── data/                         # git ignored
├── logs/                         # git ignored
├── docs/
└── images/
```

## Getting started

### 1. Clone

```bash
git clone https://github.com/Morobang/weather-data-pipeline.git
cd weather-data-pipeline
```

### 2. Generate a Fernet key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Create your .env

```bash
cp .env.example .env
# paste your Fernet key into .env
```

### 4. Start the stack

```bash
docker-compose up airflow-init
docker-compose up -d
```

### 5. Verify

- Airflow UI: http://localhost:8080 (admin / admin)
- DBeaver: connect to localhost:5432, database weather_db, user rocket

## SQL-first rule

All SQL lives in `scripts/`. Python never contains SQL strings. DAGs load `.sql` files using:

```python
def load_sql(filepath: str) -> str:
    return Path(filepath).read_text()

cursor.execute(load_sql("scripts/bronze/ddl_bronze.sql"))
```

## Author

**Morobang Tshigidimisa** · [GitHub](https://github.com/Morobang) · [Portfolio](https://morobangtshigidimisa.vercel.app)
