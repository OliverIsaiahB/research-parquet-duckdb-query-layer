"""Run our first analytical query straight against the Parquet files.

Notice what is NOT here:
- no database server to start
- no "load the CSV into a table" step
- no schema declaration in SQL

DuckDB runs in-process (like SQLite) and reads Parquet files directly. You give
read_parquet a path or a glob, and it becomes a table you can query.
"""
import duckdb


def main() -> None:
    # connect() with no path = an in-memory DuckDB. It lives only for this run.
    con = duckdb.connect()

    # read_parquet('lake/metrics/**/*.parquet') globs across ALL partition folders.
    # DuckDB also reconstructs the 'experiment' column from the folder names —
    # the partition key is queryable even though it isn't stored in the row data.
    rows = con.execute("""
        SELECT experiment, run_id, step, loss, eval_score
        FROM read_parquet('lake/metrics/**/*.parquet', hive_partitioning = true)
        ORDER BY run_id, step
        LIMIT 5
    """).fetchall()

    for r in rows:
        print(r)

    # Same idea for the flat runs file — a single Parquet file is just a table.
    n_runs = con.execute(
        "SELECT COUNT(*) FROM read_parquet('lake/runs.parquet')"
    ).fetchone()[0]
    print(f"\n{n_runs} runs in the lake")


if __name__ == "__main__":
    main()
