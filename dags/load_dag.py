import sys
import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow/dags")
from datawarehouse.data_loading import load_daily_forecast
from datawarehouse.data_transformation import run_all_verifications
from datawarehouse.soda_checks import (
    run_bronze_checks,
    run_silver_checks,
    run_gold_checks,
)

log = logging.getLogger(__name__)

default_args = {
    "owner":            "rocket",
    "retries":          1,
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

    bronze_checks_task = PythonOperator(
        task_id="bronze_quality_checks",
        python_callable=run_bronze_checks,
    )

    silver_checks_task = PythonOperator(
        task_id="silver_quality_checks",
        python_callable=run_silver_checks,
    )

    gold_checks_task = PythonOperator(
        task_id="gold_quality_checks",
        python_callable=run_gold_checks,
    )

    verify_task = PythonOperator(
        task_id="verify_all_layers",
        python_callable=run_all_verifications,
    )

    # ============================================================
    # TASK ORDER
    # load → bronze checks → silver checks → gold checks → verify
    # if any check fails the DAG stops there
    # ============================================================
    load_task >> bronze_checks_task >> silver_checks_task >> gold_checks_task >> verify_task