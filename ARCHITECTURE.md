# The Experiment Lake — Architecture

## The mess we start with
A research team runs hundreds of training jobs. Each job writes:
- `runs.jsonl`   — one JSON object per run (run_id, experiment, model, lr, started_at)
- `metrics.csv`  — one row per (run_id, step): loss, eval_score, etc.

These files pile up. To answer "what was the best eval score in the
`scaling-laws` experiment?" you currently grep CSVs by hand. That does not scale.

## What we build
A columnar query layer:

    raw logs  ->  Parquet (columnar, partitioned by experiment)  ->  DuckDB queries

## Row layout vs columnar layout (the whole idea)
CSV is ROW-oriented. On disk, row by row:

    run_1, step_0, 2.31, 0.40 | run_1, step_1, 2.10, 0.44 | run_2, step_0, ...

To compute MAX(eval_score) you must read EVERY byte of EVERY row, even the
columns you do not care about (run_id, step, loss).

Parquet is COLUMN-oriented. On disk, column by column:

    eval_score: [0.40, 0.44, 0.51, ...] | loss: [2.31, 2.10, ...] | run_id: [...]

To compute MAX(eval_score) you read ONLY the eval_score column. For wide
experiment tables with 50 metrics, that is a 50x reduction in bytes scanned.
Columns also compress far better (similar values sit next to each other).

## Why DuckDB
DuckDB is an in-process analytical database — it runs INSIDE your Python program,
like SQLite, with NO server to start. It reads Parquet files directly. You point
it at a file and run SQL. That is the entire setup.
