-- Who builds notable models? Share of each sector per year.
WITH counts AS (
    SELECT year, sector, COUNT(*) AS n
      FROM models
     WHERE sector IS NOT NULL AND year BETWEEN 2010 AND 2025
     GROUP BY year, sector
)
SELECT year, sector, n,
       ROUND(100.0 * n / SUM(n) OVER (PARTITION BY year), 1) AS pct
  FROM counts
 ORDER BY year, sector;
