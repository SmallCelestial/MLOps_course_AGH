import json
import pickle

import numpy as np
import pendulum
import polars as pl
from airflow.sdk import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.sdk import ObjectStoragePath
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVR

S3_BUCKET = "s3://taxi-data"
PROCESSED_PATH = f"{S3_BUCKET}/processed"
MODELS_PATH = f"{S3_BUCKET}/models"
BEST_MODEL_PATH = f"{S3_BUCKET}/best_model"


@task
def fetch_and_prepare_data() -> dict:
    base_path = ObjectStoragePath(PROCESSED_PATH)

    files = list(base_path.iterdir())
    files = sorted([f for f in files if str(f).endswith(".parquet")])

    print(f"Found {len(files)} parquet files:")
    for f in files:
        print(f"  - {f}")

    if len(files) < 2:
        raise ValueError(f"Need at least 2 months of processed data. Found {len(files)} files.")

    dfs = []
    for file_path in files:
        with file_path.open("rb") as f:
            df = pl.read_parquet(f)
            print(f"Loaded {file_path}: {len(df)} rows")
            dfs.append(df)

    combined_df = pl.concat(dfs).sort("date")
    print(f"Total combined rows: {len(combined_df)}")

    min_date = combined_df.select(pl.col("date").min()).item()
    max_date = combined_df.select(pl.col("date").max()).item()
    print(f"Date range: {min_date} to {max_date}")

    feature_df = combined_df.with_columns([
        pl.col("date").dt.weekday().alias("day_of_week"),
        pl.col("date").dt.day().alias("day_of_month"),
        pl.col("date").dt.month().alias("month"),
        pl.col("date").dt.year().alias("year"),
    ])

    latest_month = feature_df.select(pl.col("date").dt.month().max()).item()
    latest_year = feature_df.select(pl.col("date").dt.year().max()).item()
    print(f"Test set will use month: {latest_year}-{latest_month:02d}")

    test_mask = (pl.col("date").dt.month() == latest_month) & (pl.col("date").dt.year() == latest_year)

    train_df = feature_df.filter(~test_mask)
    test_df = feature_df.filter(test_mask)

    print(f"Train rows: {len(train_df)}, Test rows: {len(test_df)}")

    if len(train_df) == 0:
        raise ValueError("Training set is empty after split!")
    if len(test_df) == 0:
        raise ValueError("Test set is empty after split!")

    feature_cols = ["day_of_week", "day_of_month", "month", "year"]

    X_train = train_df.select(feature_cols).to_numpy()
    y_train = train_df.select("total_rides").to_numpy().ravel()
    X_test = test_df.select(feature_cols).to_numpy()
    y_test = test_df.select("total_rides").to_numpy().ravel()

    print(f"Training set size: {len(y_train)}, Test set size: {len(y_test)}")

    temp_path = ObjectStoragePath(f"{S3_BUCKET}/temp")

    data = {
        "X_train": X_train.tolist(),
        "y_train": y_train.tolist(),
        "X_test": X_test.tolist(),
        "y_test": y_test.tolist(),
        "train_size": len(y_train),
        "test_size": len(y_test),
    }

    data_path = temp_path / "train_test_data.json"
    with data_path.open("w") as f:
        json.dump(data, f)

    return {"data_path": str(data_path), "train_size": len(y_train)}


def _load_data():
    data_path = ObjectStoragePath(f"{S3_BUCKET}/temp/train_test_data.json")
    with data_path.open("r") as f:
        data = json.load(f)

    return (
        np.array(data["X_train"]),
        np.array(data["y_train"]),
        np.array(data["X_test"]),
        np.array(data["y_test"]),
        data["train_size"],
    )


@task
def train_ridge(data_info: dict) -> dict:
    X_train, y_train, X_test, y_test, train_size = _load_data()

    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)

    model_path = ObjectStoragePath(f"{MODELS_PATH}/ridge_model.pkl")
    with model_path.open("wb") as f:
        pickle.dump(model, f)

    return {
        "model_name": "Ridge",
        "mae": float(mae),
        "model_path": str(model_path),
        "train_size": train_size,
    }


@task
def train_random_forest(data_info: dict) -> dict:
    X_train, y_train, X_test, y_test, train_size = _load_data()

    param_grid = {
        "n_estimators": [50, 100],
        "max_depth": [5, 10, None],
        "min_samples_split": [2, 5],
    }

    rf = RandomForestRegressor(random_state=42)
    grid_search = GridSearchCV(
        rf, param_grid, cv=3, scoring="neg_mean_absolute_error", n_jobs=-1
    )
    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)

    model_path = ObjectStoragePath(f"{MODELS_PATH}/random_forest_model.pkl")
    with model_path.open("wb") as f:
        pickle.dump(best_model, f)

    return {
        "model_name": "RandomForest",
        "mae": float(mae),
        "model_path": str(model_path),
        "train_size": train_size,
        "best_params": grid_search.best_params_,
    }


@task
def train_svr(data_info: dict) -> dict:
    X_train, y_train, X_test, y_test, train_size = _load_data()

    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = SVR(kernel="rbf", C=100, gamma="scale")
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)

    model_data = {"model": model, "scaler": scaler}
    model_path = ObjectStoragePath(f"{MODELS_PATH}/svr_model.pkl")
    with model_path.open("wb") as f:
        pickle.dump(model_data, f)

    return {
        "model_name": "SVR",
        "mae": float(mae),
        "model_path": str(model_path),
        "train_size": train_size,
    }


@task
def select_best_model(results: list[dict]) -> dict:
    best_result = min(results, key=lambda x: x["mae"])

    best_source = ObjectStoragePath(best_result["model_path"])
    best_dest = ObjectStoragePath(f"{BEST_MODEL_PATH}/best_model.pkl")

    with best_source.open("rb") as src:
        with best_dest.open("wb") as dst:
            dst.write(src.read())

    for result in results:
        model_path = ObjectStoragePath(result["model_path"])
        model_path.unlink()

    temp_data_path = ObjectStoragePath(f"{S3_BUCKET}/temp/train_test_data.json")
    temp_data_path.unlink()

    return best_result


@task
def log_to_postgres(results: list[dict], best_result: dict):
    hook = PostgresHook(postgres_conn_id="training_db")

    training_date = pendulum.now().to_datetime_string()

    for result in results:
        is_best = result["model_name"] == best_result["model_name"]
        insert_sql = """
                     INSERT INTO model_training_log (training_date, model_name, training_set_size, test_mae, is_best)
                     VALUES (%s, %s, %s, %s, %s); \
                     """
        hook.run(insert_sql, parameters=(
            training_date,
            result["model_name"],
            result["train_size"],
            result["mae"],
            is_best,
        ))

    print(f"Logged {len(results)} model results to Postgres")
    print(f"Best model: {best_result['model_name']} with MAE: {best_result['mae']}")


@dag(
    dag_id="train_models_pipeline",
    start_date=pendulum.datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    default_args={
        "retries": 2,
        "retry_delay": pendulum.duration(minutes=5),
    },
)
def train_models_pipeline():
    data_info = fetch_and_prepare_data()

    ridge_result = train_ridge(data_info)
    rf_result = train_random_forest(data_info)
    svr_result = train_svr(data_info)

    all_results = [ridge_result, rf_result, svr_result]

    best = select_best_model(all_results)

    log_to_postgres(all_results, best)


train_models_pipeline()


