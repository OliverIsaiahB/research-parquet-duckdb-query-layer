"""Write the loaded tables to Parquet, with an EXPLICIT schema.

Why explicit? Inferred schemas drift. If one day a metric file has no eval_score
rows, inference might guess the wrong type. Declaring the schema up front makes
the storage layer stable — every write produces the same column types.

We also PARTITION the metrics by experiment. Partitioning writes one sub-folder
per experiment value, so a query filtered to one experiment only opens that
folder's files. It is a physical pre-filter baked into the directory layout.
"""
import pyarrow as pa
import pyarrow.parquet as pq

from ingest import load_runs, load_metrics

# An explicit schema = the contract for what's on disk. Types are fixed here,
# not guessed at write time.
RUNS_SCHEMA = pa.schema([
    ("run_id", pa.string()),
    ("experiment", pa.string()),
    ("model", pa.string()),
    ("lr", pa.float64()),
    ("started_at", pa.timestamp("ns")),
])

METRICS_SCHEMA = pa.schema([
    ("run_id", pa.string()),
    ("experiment", pa.string()),   # denormalized in so we can PARTITION by it
    ("step", pa.int64()),
    ("loss", pa.float64()),
    ("eval_score", pa.float64()),
])


def write_all(out_dir: str = "lake") -> None:
    runs = load_runs()
    metrics = load_metrics()

    # Join experiment onto metrics so each metric row knows its experiment.
    # That column becomes the partition key.
    metrics = metrics.merge(runs[["run_id", "experiment"]], on="run_id", how="left")

    # Build PyArrow tables AGAINST our schema. If a column's type doesn't match,
    # this raises — which is exactly the early failure we want.
    runs_table = pa.Table.from_pandas(runs, schema=RUNS_SCHEMA, preserve_index=False)
    metrics_table = pa.Table.from_pandas(metrics, schema=METRICS_SCHEMA, preserve_index=False)

    # runs is small: one flat file.
    pq.write_table(runs_table, f"{out_dir}/runs.parquet")

    # metrics is partitioned: lake/metrics/experiment=scaling-laws/*.parquet etc.
    pq.write_to_dataset(
        metrics_table,
        root_path=f"{out_dir}/metrics",
        partition_cols=["experiment"],
    )
    print(f"Wrote Parquet to {out_dir}/  (runs.parquet + partitioned metrics/)")


if __name__ == "__main__":
    write_all()
