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

DROP VIEW IF EXISTS total_state_from_cities;
CREATE VIEW total_state_from_cities AS
	SELECT
		date,
		state,
		SUM(confirmed) AS confirmed,
		SUM(deaths) AS deaths
	FROM caso
	WHERE
		is_last = 'True'
		AND place_type = 'city'
	GROUP BY
		state
	ORDER BY
		state;

DROP VIEW IF EXISTS total_state_from_states;
CREATE VIEW total_state_from_states AS
	SELECT
		date,
		state,
		confirmed,
		deaths
	FROM caso
	WHERE
		is_last = 'True'
		AND place_type = 'state'
	ORDER BY
		state;

DROP VIEW IF EXISTS total_from_state_and_cities;
CREATE VIEW total_from_state_and_cities AS
	SELECT
		c.state,
		c.confirmed AS confirmed_cities,
		c.deaths AS deaths_cities,
		s.confirmed AS confirmed_state,
		s.deaths AS deaths_state
	FROM total_state_from_cities AS c
		JOIN total_state_from_states AS s
		ON
			c.state = s.state;
