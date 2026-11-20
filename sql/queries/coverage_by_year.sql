-- How many models per year have a training-compute estimate? Needed to judge selection bias.
SELECT year,
       COUNT(*)                                             AS models,
       SUM(compute_flop IS NOT NULL)                        AS with_compute,
       ROUND(100.0 * SUM(compute_flop IS NOT NULL) / COUNT(*), 1) AS pct_with_compute
  FROM models
 WHERE year BETWEEN 2010 AND 2025
 GROUP BY year
 ORDER BY year;
