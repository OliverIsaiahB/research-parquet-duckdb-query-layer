"""Read the raw research logs into memory.

Two different shapes:
- runs.jsonl  : ONE row per training run (the run's metadata)
- metrics.csv : MANY rows per run (one row per logged step)

We load each with pandas (easy, forgiving) and also show the PyArrow Table,
since Parquet is a PyArrow-native format and we'll write it with PyArrow next.
"""
import pandas as pd
import pyarrow as pa


def load_runs(path: str = "sample_data/runs.jsonl") -> pd.DataFrame:
    # lines=True tells pandas this is JSONL: one JSON object per line,
    # NOT one big JSON array. This is how most loggers write run records.
    runs = pd.read_json(path, lines=True)
    # Parse the date string into a real datetime so we can partition / filter on it.
    runs["started_at"] = pd.to_datetime(runs["started_at"])
    return runs


def load_metrics(path: str = "sample_data/metrics.csv") -> pd.DataFrame:
    # CSV is row-oriented and forgiving; pandas infers the numeric dtypes.
    return pd.read_csv(path)


if __name__ == "__main__":
    runs = load_runs()
    metrics = load_metrics()

    print("runs (one row per run):")
    print(runs)
    print("\nmetrics (many rows per run):")
    print(metrics.head())

    # A PyArrow Table is the in-memory columnar representation Parquet maps to.
    # Converting now lets us SEE the inferred schema before we commit to one.
    metrics_table = pa.Table.from_pandas(metrics)
    print("\nPyArrow-inferred metrics schema:")
    print(metrics_table.schema)
