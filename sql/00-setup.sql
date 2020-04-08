CREATE INDEX IF NOT EXISTS idx_caso_key ON caso (
	date,
	state,
	city,
	place_type
);
UPDATE caso SET city = '' WHERE place_type = 'state';  /* Remove NULLs */

CREATE INDEX IF NOT EXISTS idx_caso_full_key ON caso_full (
	date,
	state,
	city,
	place_type
);
UPDATE caso_full SET city = '' WHERE place_type = 'state';  /* Remove NULLs */

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
		place_type,
		city_ibge_code,
		estimated_population_2019
	FROM
		caso_full
	GROUP BY
		state,
		city,
		place_type,
		city_ibge_code,
		estimated_population_2019;

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

DROP VIEW IF EXISTS city_cases;
CREATE VIEW city_cases AS
	SELECT
		*
	FROM caso_full
	WHERE
		place_type = 'city'
		AND had_cases = 'True';
