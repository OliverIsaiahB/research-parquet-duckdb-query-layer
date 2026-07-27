-- Real questions a researcher asks, as SQL over the Parquet lake.
-- Run with: duckdb < research_queries.sql   (no database file needed)

-- Q1: Best eval score reached in each experiment.
-- "Which experiment is winning?"
SELECT
    experiment,
    MAX(eval_score) AS best_eval
FROM read_parquet('lake/metrics/**/*.parquet', hive_partitioning = true)
GROUP BY experiment
ORDER BY best_eval DESC;

-- Q2: How many distinct runs per experiment.
-- "How much did we actually try in each direction?"
SELECT
    experiment,
    COUNT(DISTINCT run_id) AS n_runs,
    COUNT(*)               AS n_metric_rows
FROM read_parquet('lake/metrics/**/*.parquet', hive_partitioning = true)
GROUP BY experiment;

-- Q3: Best run per experiment, joined back to the run metadata (model, lr).
-- "What hyperparameters produced the best result?"
WITH best AS (
    SELECT run_id, MAX(eval_score) AS best_eval
    FROM read_parquet('lake/metrics/**/*.parquet', hive_partitioning = true)
    GROUP BY run_id
)
SELECT r.experiment, r.run_id, r.model, r.lr, b.best_eval
FROM best b
JOIN read_parquet('lake/runs.parquet') r USING (run_id)
ORDER BY b.best_eval DESC
LIMIT 5;
