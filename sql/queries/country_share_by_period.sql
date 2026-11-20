-- Country of the developing organization (first listed), grouped into US / China / UK / Other.
WITH base AS (
    SELECT CASE WHEN year BETWEEN 2010 AND 2017 THEN '2010-2017'
                WHEN year BETWEEN 2018 AND 2021 THEN '2018-2021'
                ELSE '2022-2025' END AS period,
           CASE WHEN country = 'United States of America' THEN 'United States'
                WHEN country = 'China' THEN 'China'
                WHEN country LIKE 'United Kingdom%' THEN 'United Kingdom'
                ELSE 'Other' END AS country_group
      FROM models
     WHERE country IS NOT NULL AND year BETWEEN 2010 AND 2025
)
SELECT period, country_group, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY period), 1) AS pct
  FROM base
 GROUP BY period, country_group
 ORDER BY period, n DESC;
