import datetime
import json
import pendulum
from airflow.providers.postgres.hooks.postgres import PostgresHook

from airflow.providers.standard.operators.python import PythonVirtualenvOperator, PythonOperator
from airflow.sdk import Variable

from airflow import DAG


def get_data(data_interval_start: pendulum.DateTime, td_api_key) -> dict:
    import os
    from twelvedata import TDClient

    td = TDClient(apikey=td_api_key)

    ts = td.exchange_rate(symbol="USD/EUR", date=data_interval_start.isoformat())
    data = ts.as_json()
    return data


def save_data(data: dict) -> None:
    print("Saving the data")
    POSTGRES_CONN_ID = "postgres_storage"
    pg_hook = PostgresHook.get_hook(POSTGRES_CONN_ID)

    if not data:
        raise ValueError("No data received")

    sql = """
          INSERT INTO exchange_rates (symbol, rate)
          VALUES (%(symbol)s, %(rate)s); \
          """

    parameters = {
        "symbol": data["symbol"],
        "rate": float(data["rate"])
    }

    pg_hook.run(sql, parameters=parameters)


with DAG(
    dag_id="connections_and_variables",
    start_date=pendulum.datetime(2026, 1, 15),
    schedule=datetime.timedelta(days=1),
) as dag:
    get_data_op = PythonVirtualenvOperator(
        task_id="get_data",
        python_callable=get_data,
        requirements=["twelvedata", "pendulum", "lazy_object_proxy"],
        serializer="cloudpickle",
        op_kwargs={"td_api_key": Variable.get("TWELVEDATA_API_KEY")},

    )

    save_data_op = PythonOperator(
        task_id="save_data",
        python_callable=save_data,
        op_kwargs={"data": get_data_op.output},
    )

    get_data_op >> save_data_op
