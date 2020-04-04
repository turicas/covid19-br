CREATE INDEX IF NOT EXISTS idx_caso_key ON caso (
	date,
	state,
	city,
	place_type
);
UPDATE caso SET city = '' WHERE place_type = 'state';  /* Remove NULLs */

DROP VIEW IF EXISTS all_dates;
CREATE VIEW all_dates AS
	SELECT
		DISTINCT date
	FROM
		caso
	ORDER BY
		date ASC;

DROP VIEW IF EXISTS all_places;
CREATE VIEW all_places AS
	SELECT
		state,
		city,
		'city' AS place_type,
		city_ibge_code,
		estimated_population AS estimated_population_2019
	FROM
		populacao_estimada_2019
	UNION
	SELECT
		state,
		'' AS city,
		'state' AS place_type,
		state_ibge_code AS city_ibge_code,
		SUM(estimated_population) AS estimated_population_2019
	FROM populacao_estimada_2019
	GROUP BY state;

DROP VIEW IF EXISTS place_date_matrix;
CREATE VIEW place_date_matrix AS
	SELECT
		d.date,
		p.state,
		p.city,
		p.place_type,
		p.city_ibge_code,
		p.estimated_population_2019
	FROM all_dates AS d
		JOIN all_places AS p;

DROP VIEW IF EXISTS ultimas_atualizacoes;
CREATE VIEW ultimas_atualizacoes AS
	SELECT
		MAX(date) AS last_date,
		state,
		city,
		place_type,
		MAX(order_for_place) AS last_order_for_place
	FROM caso
	GROUP BY
		state,
		city,
		place_type
	ORDER BY
		last_date,
		state,
		city;
