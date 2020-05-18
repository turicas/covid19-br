DROP VIEW IF EXISTS new_cases_per_state;
CREATE VIEW new_cases_per_state AS
	SELECT
		epidemiological_week,
		state,
		SUM(new_confirmed) AS new_confirmed,
		SUM(new_deaths) AS new_deaths
	FROM caso_full
	WHERE
		place_type = 'state'
	GROUP BY
		epidemiological_week,
		state;

DROP VIEW IF EXISTS new_cases;
CREATE VIEW new_cases AS
	SELECT
		epidemiological_week,
		SUM(new_confirmed) AS new_confirmed,
		SUM(new_deaths) AS new_deaths
	FROM caso_full
	WHERE
		place_type = 'state'
	GROUP BY
		epidemiological_week;
