import sys
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow/dags")
from datawarehouse.data_loading import load_daily_forecast
from datawarehouse.data_transformation import run_all_verifications

log = logging.getLogger(__name__)

default_args = {
    "owner":            "rocket",
    "retries":          3,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="load_weather",
    description="Load SA weather JSON into Bronze → Silver → Gold",
    default_args=default_args,
    start_date=datetime(2026, 6, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["weather", "loading", "silver", "gold"],
) as dag:

    load_task = PythonOperator(
        task_id="load_daily_forecast",
        python_callable=load_daily_forecast,
    )

    verify_task = PythonOperator(
        task_id="verify_all_layers",
        python_callable=run_all_verifications,
    )

    # load first then verify
    load_task >> verify_task