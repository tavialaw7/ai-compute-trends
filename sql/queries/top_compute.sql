-- The ten largest training runs in the dataset.
SELECT model, organization, pub_date, sector, accessibility, compute_flop
  FROM models
 WHERE compute_flop IS NOT NULL
 ORDER BY compute_flop DESC
 LIMIT 10;
