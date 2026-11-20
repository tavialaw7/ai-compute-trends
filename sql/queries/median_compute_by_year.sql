-- Median training compute per year (average of the two middle rows for even counts).
WITH ranked AS (
    SELECT year, compute_flop,
           ROW_NUMBER() OVER (PARTITION BY year ORDER BY compute_flop) AS rn,
           COUNT(*)     OVER (PARTITION BY year)                       AS cnt
      FROM models
     WHERE compute_flop IS NOT NULL AND year BETWEEN 2010 AND 2025
)
SELECT year, MAX(cnt) AS n, AVG(compute_flop) AS median_flop
  FROM ranked
 WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
 GROUP BY year
 ORDER BY year;
