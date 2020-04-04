SELECT
	date,
	COUNT(*) AS novos_municipios,
	GROUP_CONCAT(city_ibge_code) AS codigo_ibge_municipios,
	GROUP_CONCAT(city || '/' || state) AS municipios,
	SUM(estimated_population_2019) AS populacao_2019_afetada
FROM caso
WHERE
	place_type = 'city'
	AND order_for_place = 1
	AND city != 'Importados/Indefinidos'
GROUP BY date
ORDER BY date ASC;
