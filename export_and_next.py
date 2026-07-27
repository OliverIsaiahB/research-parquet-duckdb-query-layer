"""Export a query result so a collaborator can use it without your code.

A summary is itself just data. We write it back out as Parquet (for another
DuckDB/pandas user) AND as CSV (for a spreadsheet). DuckDB's COPY ... TO does
this in one statement, straight from a query — the result never has to round-trip
through pandas.
"""
import duckdb

from research_lake import experiment_summary


def export_summary(out_stem: str = "exports/experiment_summary") -> None:
    con = duckdb.connect()

    # COPY (<query>) TO '<path>' writes the query result directly to disk.
    # FORMAT PARQUET keeps it columnar for downstream tools; CSV for humans.
    con.execute(f"""
        COPY (
            SELECT experiment, COUNT(DISTINCT run_id) AS n_runs, MAX(eval_score) AS best_eval
            FROM read_parquet('lake/metrics/**/*.parquet', hive_partitioning=true, union_by_name=true)
            GROUP BY experiment
        ) TO '{out_stem}.parquet' (FORMAT PARQUET);
    """)
    con.execute(f"""
        COPY (SELECT * FROM read_parquet('{out_stem}.parquet'))
        TO '{out_stem}.csv' (FORMAT CSV, HEADER);
    """)
    print(f"Wrote {out_stem}.parquet and {out_stem}.csv")

    # Sanity: read the just-written Parquet back through our own module's idea.
    print(experiment_summary())


if __name__ == "__main__":
    export_summary()
