"""Reality: logs change over time. A new training run starts logging grad_norm,
a column the older Parquet files never had. We must NOT have to rewrite history.

DuckDB handles this with union_by_name=true: it matches columns by NAME across
files, and fills missing columns with NULL. This is 'schema-on-read' — the schema
is reconciled when you query, not frozen when you wrote.
"""
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd


def add_v2_partition(out_dir: str = "lake") -> None:
    # The new file has an EXTRA column: grad_norm.
    df = pd.read_csv("sample_data/metrics_v2.csv")
    df["experiment"] = "rlhf-reward"   # these new runs belong to this experiment
    table = pa.Table.from_pandas(df, preserve_index=False)
    # Write it into the same dataset. Old partitions have no grad_norm; that's fine.
    pq.write_to_dataset(table, root_path=f"{out_dir}/metrics", partition_cols=["experiment"])


def query_mixed_schema() -> None:
    con = duckdb.connect()
    # union_by_name = true aligns columns by name across files of DIFFERENT schemas.
    # Files without grad_norm contribute NULL for it. COALESCE gives a default,
    # and TRY_CAST safely coerces types without crashing on a bad value.
    rows = con.execute("""
        SELECT
            run_id,
            step,
            eval_score,
            COALESCE(TRY_CAST(grad_norm AS DOUBLE), 0.0) AS grad_norm
        FROM read_parquet(
            'lake/metrics/**/*.parquet',
            hive_partitioning = true,
            union_by_name = true
        )
        ORDER BY run_id, step
    """).fetchall()
    for r in rows:
        print(r)


if __name__ == "__main__":
    add_v2_partition()
    query_mixed_schema()
