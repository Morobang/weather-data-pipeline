from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
sys.path.insert(0, "/opt/airflow/dags")
from api.weather_extract import extract_all_cities

default_args = {
    "owner":            "rocket",
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="extract_weather",
    description="Extract SA weather data from Open-Meteo API — 9 provinces, 38 cities",
    default_args=default_args,
    start_date=datetime(2026, 6, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["weather", "extraction", "bronze"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_all_cities",
        python_callable=extract_all_cities,
    )
