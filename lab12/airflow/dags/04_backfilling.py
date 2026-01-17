import datetime
import pandas as pd
import requests
from airflow.sdk import dag, task


@dag(
    dag_id="new_york_max_min_temperature_gathering",
    start_date=datetime.datetime(2025, 1, 1),
    end_date=datetime.datetime(2025, 1, 31),
    schedule=datetime.timedelta(days=7),
    catchup=True
)
def max_min_temperature_pipeline():
    @task(task_id="get_data")
    def get_data(logical_date) -> dict:
        start_date = logical_date.strftime("%Y-%m-%d")
        end_date = (logical_date + datetime.timedelta(days=6)).strftime("%Y-%m-%d")
        print(f"Fetching data from API for {start_date} to {end_date}")

        url = f"https://historical-forecast-api.open-meteo.com/v1/forecast?latitude=40.7143&longitude=-74.006&start_date={start_date}&end_date={end_date}&hourly=temperature_2m&timezone=auto"

        resp = requests.get(url)
        resp.raise_for_status()

        return resp.json()["hourly"]

    @task(task_id="transform")
    def transform(data: dict) -> pd.DataFrame:
        df = pd.DataFrame(data)
        df["time"] = pd.to_datetime(df["time"])
        df["date"] = df["time"].dt.date

        daily_temps = df.groupby("date")["temperature_2m"].agg(["min", "max"]).reset_index()
        daily_temps.rename(columns={"min": "min_temperature", "max": "max_temperature"}, inplace=True)

        print("Transformed data:")
        print(daily_temps.head())
        return daily_temps

    @task(task_id="load")
    def save_data(df: pd.DataFrame, logical_date) -> None:
        start_date = logical_date.strftime("%Y-%m-%d")
        filename = f"min_max_temperature_{start_date}.csv"
        print(f"Saving the data to {filename}")
        df.to_csv(filename, index=False)

    data = get_data()
    transformed_data = transform(data)
    save_data(transformed_data)


max_min_temperature_pipeline()
