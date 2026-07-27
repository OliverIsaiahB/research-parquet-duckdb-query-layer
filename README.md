# The Experiment Lake — A Parquet + DuckDB Query Layer for ML Research Logs

Every ML team drowns in raw experiment logs — JSONL run records, CSV metric dumps, one folder per training job. This project teaches you to turn that mess into a real analytical query layer. You will read raw runs.jsonl and metrics.csv into pandas and PyArrow, write them to columnar Parquet with an explicit schema partitioned by experiment, then query them directly with DuckDB — no database server, no load step. You will run the aggregations researchers actually run (best eval score per experiment, run counts, loss histories), handle schema evolution when a new metric column appears in later logs, and wrap the SQL in a tiny reusable Python query module. This is the storage and query foundation that a full ML research data platform sits on: the later rungs add an ingestion API and a serving layer, but they all read from the Parquet substrate you build here.

Built step-by-step with [KhwajaLabs Build](https://khwajalabs.com).

## Stack
- Python
- DuckDB
- Parquet
- PyArrow
- pandas
