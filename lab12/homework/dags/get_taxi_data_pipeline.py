import pendulum
import polars as pl
import requests
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import ObjectStoragePath


def download_taxi_data(logical_date: pendulum.DateTime) -> str:
    year = logical_date.year
    month = logical_date.month

    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"

    print(f"Downloading taxi data for {year}-{month:02d}")
    response = requests.get(url)
    response.raise_for_status()

    base = ObjectStoragePath("s3://taxi-data/raw")
    path = base / f"yellow_tripdata_{year}-{month:02d}.parquet"

    with path.open("wb") as f:
        f.write(response.content)

    print(f"Saved raw data to {path}")
    return str(path)


def process_taxi_data(logical_date: pendulum.DateTime) -> str:
    year = logical_date.year
    month = logical_date.month

    raw_path = ObjectStoragePath("s3://taxi-data/raw") / f"yellow_tripdata_{year}-{month:02d}.parquet"

    print(f"Processing taxi data for {year}-{month:02d}")

    with raw_path.open("rb") as f:
        df = pl.read_parquet(f)

    start_date = pendulum.datetime(year, month, 1).date()
    if month == 12:
        end_date = pendulum.datetime(year + 1, 1, 1).date()
    else:
        end_date = pendulum.datetime(year, month + 1, 1).date()

    processed_df = (
        df
        .with_columns(
            pl.col("tpep_pickup_datetime").dt.date().alias("date")
        )
        .filter(
            (pl.col("date") >= start_date) & (pl.col("date") < end_date)
        )
        .group_by("date")
        .agg(
            pl.count().alias("total_rides")
        )
        .sort("date")
    )

    processed_base = ObjectStoragePath("s3://taxi-data/processed")
    processed_path = processed_base / f"daily_rides_{year}-{month:02d}.parquet"

    with processed_path.open("wb") as f:
        processed_df.write_parquet(f)

    print(f"Saved processed data to {processed_path}")
    print(f"Processed {len(processed_df)} days of data")

    return str(processed_path)


with DAG(
        dag_id="taxi_data_pipeline",
        start_date=pendulum.datetime(2025, 1, 1),
        end_date=pendulum.datetime(2025, 11, 1),
        schedule="@monthly",
        catchup=True,
        max_active_runs=3,
        default_args={
            "retries": 2,
            "retry_delay": pendulum.duration(minutes=5),
        },
):
    download_task = PythonOperator(
        task_id="download_taxi_data",
        python_callable=download_taxi_data,
    )

    process_task = PythonOperator(
        task_id="process_taxi_data",
        python_callable=process_taxi_data,
    )

    download_task >> process_task
