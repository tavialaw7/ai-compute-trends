-- Share of models with open weights, among models where Epoch records the answer.
SELECT year,
       COUNT(*)          AS known,
       SUM(open_weights) AS open_models,
       ROUND(100.0 * SUM(open_weights) / COUNT(*), 1) AS pct_open
  FROM models
 WHERE open_weights IS NOT NULL AND year BETWEEN 2018 AND 2025
 GROUP BY year
 ORDER BY year;
