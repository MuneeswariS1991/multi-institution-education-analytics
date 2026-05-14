from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import logging
import os
import sys

# =====================================
# PATHS
# =====================================
DAG_FOLDER = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = r"C:\Users\sanac\PycharmProjects\PythonProject\multi_institution_education_analytics"

LOG_FILE = os.path.join(DAG_FOLDER, "job_run_status.log")

# create dags folder log file automatically
os.makedirs(DAG_FOLDER, exist_ok=True)

# =====================================
# LOGGER CONFIGURATION
# =====================================
logger = logging.getLogger("student_dbt_pipeline")
logger.setLevel(logging.INFO)

# remove duplicate handlers
if logger.hasHandlers():
    logger.handlers.clear()

# file handler -> saves log in file
file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")

# stdout handler -> avoids red color
console_handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter(
    "%(asctime)s | DAG: student_dbt_daily_pipeline | %(levelname)s | %(message)s"
)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

print(f"Log file location: {LOG_FILE}")

# =====================================
# DEFAULT ARGS
# =====================================
default_args = {
    "owner": "sanac",
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

# =====================================
# WRITE STATUS TO LOG FILE
# =====================================
def write_status_log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {message}\n")

# =====================================
# COMMON DBT EXECUTOR
# =====================================
def execute_dbt(command, task_name):
    logger.info(f"{task_name} STARTED")
    write_status_log(f"{task_name} STARTED")

    result = subprocess.run(
        command,
        cwd=PROJECT_PATH,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.stdout:
        logger.info(result.stdout)
        write_status_log(result.stdout)

    if result.stderr:
        logger.error(result.stderr)
        write_status_log(result.stderr)

    if result.returncode != 0:
        logger.error(f"{task_name} FAILED")
        write_status_log(f"{task_name} FAILED")
        raise Exception(result.stderr)

    logger.info(f"{task_name} SUCCESS")
    write_status_log(f"{task_name} SUCCESS")

# =====================================
# TASK FUNCTIONS
# =====================================
def run_dbt():
    execute_dbt(
        "dbt run --select student_incremental",
        "DBT_RUN"
    )

def test_dbt():
    execute_dbt(
        "dbt test --select student_incremental",
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
    try:
        logger.info("PIPELINE STARTED")
        write_status_log("PIPELINE STARTED")

        run_dbt()
        test_dbt()

        logger.info("PIPELINE SUCCESS")
        write_status_log("PIPELINE SUCCESS")

    except Exception as e:
        logger.error(f"PIPELINE FAILED: {e}")
        write_status_log(f"PIPELINE FAILED: {e}")