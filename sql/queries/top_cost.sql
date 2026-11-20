-- The ten most expensive training runs where Epoch estimates cost (2023 USD).
SELECT model, organization, pub_date, cost_usd_2023, compute_flop
  FROM models
 WHERE cost_usd_2023 IS NOT NULL
 ORDER BY cost_usd_2023 DESC
 LIMIT 10;
