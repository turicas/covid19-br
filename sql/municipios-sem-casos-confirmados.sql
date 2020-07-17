SELECT
  c.state,
  c.city
FROM populacao_estimada_2019 AS c
  LEFT JOIN (
    SELECT DISTINCT state, city
    FROM caso
    WHERE place_type = 'city' AND city_ibge_code != '' AND confirmed > 0 AND is_last = 'True'
  ) AS ccc
    ON ccc.state = c.state AND ccc.city = c.city
WHERE ccc.state IS NULL AND ccc.city IS NULL
ORDER BY c.state, c.city;
