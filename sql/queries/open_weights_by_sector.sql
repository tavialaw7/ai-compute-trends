-- Openness by sector, 2022-2025 (known values only).
SELECT sector,
       COUNT(*)          AS known,
       SUM(open_weights) AS open_models,
       ROUND(100.0 * SUM(open_weights) / COUNT(*), 1) AS pct_open
  FROM models
 WHERE open_weights IS NOT NULL AND sector IS NOT NULL AND year BETWEEN 2022 AND 2025
 GROUP BY sector
 ORDER BY known DESC;
