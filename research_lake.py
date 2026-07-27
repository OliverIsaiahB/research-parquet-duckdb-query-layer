"""The public query API of the lake.

Everything above was exploration. THIS is the seam later rungs import: a small,
stable set of functions that hide the SQL and the file paths. An ingestion API
(next rung) writes Parquet into the lake; a serving layer queries through these
functions. Nobody downstream has to know the directory layout.
"""
import duckdb
import pandas as pd

LAKE = "lake"
METRICS = f"read_parquet('{LAKE}/metrics/**/*.parquet', hive_partitioning=true, union_by_name=true)"
RUNS = f"read_parquet('{LAKE}/runs.parquet')"


def _con() -> duckdb.DuckDBPyConnection:
    # One fresh in-process connection per call keeps this stateless and safe.
    return duckdb.connect()


def top_runs(limit: int = 5) -> pd.DataFrame:
    """Best run by peak eval_score, with its hyperparameters. Returns a DataFrame."""
    return _con().execute(f"""
        WITH best AS (
            SELECT run_id, MAX(eval_score) AS best_eval
            FROM {METRICS} GROUP BY run_id
        )
        SELECT r.experiment, r.run_id, r.model, r.lr, b.best_eval
        FROM best b JOIN {RUNS} r USING (run_id)
        ORDER BY b.best_eval DESC
        LIMIT ?
    """, [limit]).df()


def metric_history(run_id: str, metric: str = "eval_score") -> pd.DataFrame:
    """The step-by-step curve of one metric for one run (e.g. a loss curve)."""
    # The metric NAME is validated against an allowlist — never f-string raw
    # user input into SQL as a column name. Values use parameters (?) instead.
    allowed = {"loss", "eval_score", "grad_norm"}
    if metric not in allowed:
        raise ValueError(f"unknown metric {metric!r}; allowed: {sorted(allowed)}")
    return _con().execute(f"""
        SELECT step, {metric} AS value
        FROM {METRICS}
        WHERE run_id = ?
        ORDER BY step
    """, [run_id]).df()


def experiment_summary() -> pd.DataFrame:
    """One row per experiment: run count and best eval score."""
    return _con().execute(f"""
        SELECT
            experiment,
            COUNT(DISTINCT run_id) AS n_runs,
            MAX(eval_score)        AS best_eval
        FROM {METRICS}
        GROUP BY experiment
        ORDER BY best_eval DESC
    """).df()


if __name__ == "__main__":
    print("== experiment_summary ==")
    print(experiment_summary())
    print("\n== top_runs ==")
    print(top_runs())
    print("\n== metric_history(r-001) ==")
    print(metric_history("r-001"))
