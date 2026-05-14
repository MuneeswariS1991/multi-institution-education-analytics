import os
import sys
import logging
import subprocess
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# =====================================
# PATHS
# =====================================
DAG_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = r"C:\Users\sanac\PycharmProjects\PythonProject\multi_institution_education_analytics"
LOG_FILE = os.path.join(DAG_FOLDER, "job_run_status.log")

# =====================================
# LOGGER
# =====================================
logger = logging.getLogger("student_dbt_pipeline")
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

formatter = logging.Formatter(
    "%(asctime)s | DAG: student_dbt_daily_pipeline | %(levelname)s | %(message)s"
)

file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
console_handler = logging.StreamHandler(sys.stdout)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# =====================================
# DEFAULT ARGS
# =====================================
default_args = {
    "owner": "sanac",
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

# =====================================
# DBT EXECUTION
# =====================================
def execute_dbt(command, task_name):
    logger.info(f"{task_name} STARTED")

    result = subprocess.run(
        command,
        cwd=PROJECT_PATH,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.stdout:
        logger.info(result.stdout)

    if result.stderr:
        logger.error(result.stderr)

    if result.returncode != 0:
        logger.error(f"{task_name} FAILED")
        raise Exception(result.stderr)

    logger.info(f"{task_name} SUCCESS")


def run_dbt():
    execute_dbt(
        "dbt run --select student_incremental --no-use-colors",
        "DBT_RUN"
    )


def test_dbt():
    execute_dbt(
        "dbt test --select student_incremental --no-use-colors",
        "DBT_TEST"
    )

# =====================================
# DAG
# =====================================
dag = DAG(
    dag_id="student_dbt_daily_pipeline",
    default_args=default_args,
    schedule="@daily",
    start_date=datetime(2026, 4, 2),
    catchup=False
)

dbt_run_task = PythonOperator(
    task_id="dbt_run",
    python_callable=run_dbt,
    dag=dag
)

dbt_test_task = PythonOperator(
    task_id="dbt_test",
    python_callable=test_dbt,
    dag=dag
)

dbt_run_task >> dbt_test_task

# =====================================
# LOCAL EXECUTION
# =====================================
if __name__ == "__main__":
    logger.info("PIPELINE STARTED")
    run_dbt()
    test_dbt()
    logger.info("PIPELINE SUCCESS")