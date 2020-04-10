DROP VIEW IF EXISTS deaths_brazil_by_arpen_per_day;
CREATE VIEW deaths_brazil_by_arpen_per_day AS
	SELECT
		date,
		epidemiological_week_2020 AS epidemiological_week,
		SUM(new_deaths_respiratory_failure_2020) AS new_deaths_respiratory_failure,
		SUM(deaths_respiratory_failure_2020) AS deaths_respiratory_failure,
		SUM(new_deaths_pneumonia_2020) AS new_deaths_pneumonia,
		SUM(deaths_pneumonia_2020) AS deaths_pneumonia,
		SUM(new_deaths_covid19) AS new_deaths_covid19,
		SUM(deaths_covid19) AS deaths_covid19
	FROM obito_cartorio
	GROUP BY
		date
	ORDER BY
		date;

DROP VIEW IF EXISTS deaths_by_arpen_per_week_2020;
CREATE VIEW deaths_by_arpen_per_week_2020 AS
	SELECT
		state,
		epidemiological_week_2020 AS epidemiological_week,
		SUM(new_deaths_respiratory_failure_2020) AS new_deaths_respiratory_failure,
		MAX(deaths_respiratory_failure_2020) AS deaths_respiratory_failure,
		SUM(new_deaths_pneumonia_2020) AS new_deaths_pneumonia,
		MAX(deaths_pneumonia_2020) AS deaths_pneumonia,
		SUM(new_deaths_covid19) AS new_deaths_covid19,
		MAX(deaths_covid19) AS deaths_covid19
	FROM obito_cartorio
	GROUP BY
		epidemiological_week,
		state
	ORDER BY
		epidemiological_week,
		state;

DROP VIEW IF EXISTS deaths_by_arpen_per_week_2019;
CREATE VIEW deaths_by_arpen_per_week_2019 AS
	SELECT
		state,
		epidemiological_week_2019 AS epidemiological_week,
		SUM(new_deaths_respiratory_failure_2019) AS new_deaths_respiratory_failure,
		MAX(deaths_respiratory_failure_2019) AS deaths_respiratory_failure,
		SUM(new_deaths_pneumonia_2019) AS new_deaths_pneumonia,
		MAX(deaths_pneumonia_2019) AS deaths_pneumonia,
		0 AS new_deaths_covid19,
		0 AS deaths_covid19
	FROM obito_cartorio
	GROUP BY
		epidemiological_week,
		state
	ORDER BY
		epidemiological_week,
		state;

DROP VIEW IF EXISTS deaths_by_arpen_per_week;
CREATE VIEW deaths_by_arpen_per_week AS
	SELECT
		c.state,
		c.epidemiological_week,
		c.new_deaths_respiratory_failure AS new_deaths_respiratory_failure_2020,
		c.deaths_respiratory_failure AS deaths_respiratory_failure_2020,
		l.new_deaths_respiratory_failure AS new_deaths_respiratory_failure_2019,
		l.deaths_respiratory_failure AS deaths_respiratory_failure_2019,
		c.new_deaths_pneumonia AS new_deaths_pneumonia_2020,
		c.deaths_pneumonia AS deaths_pneumonia_2020,
		l.new_deaths_pneumonia AS new_deaths_pneumonia_2019,
		l.deaths_pneumonia AS deaths_pneumonia_2019,
		c.new_deaths_covid19 AS new_deaths_covid19_2020,
		c.deaths_covid19 AS deaths_covid19_2020,
		l.new_deaths_covid19 AS new_deaths_covid19_2019,
		l.deaths_covid19 AS deaths_covid19_2019
	FROM deaths_by_arpen_per_week_2020 AS c
		JOIN deaths_by_arpen_per_week_2019 AS l
			ON c.state = l.state AND c.epidemiological_week = l.epidemiological_week;

DROP VIEW IF EXISTS deaths_brazil_by_arpen_per_week;
CREATE VIEW deaths_brazil_by_arpen_per_week AS
	SELECT
		epidemiological_week,
		SUM(new_deaths_respiratory_failure_2020) AS new_deaths_respiratory_failure_2020,
		SUM(deaths_respiratory_failure_2020) AS deaths_respiratory_failure_2020,
		SUM(new_deaths_respiratory_failure_2019) AS new_deaths_respiratory_failure_2019,
		SUM(deaths_respiratory_failure_2019) AS deaths_respiratory_failure_2019,
		SUM(new_deaths_pneumonia_2020) AS new_deaths_pneumonia_2020,
		SUM(deaths_pneumonia_2020) AS deaths_pneumonia_2020,
		SUM(new_deaths_pneumonia_2019) AS new_deaths_pneumonia_2019,
		SUM(deaths_pneumonia_2019) AS deaths_pneumonia_2019,
		SUM(new_deaths_covid19_2020) AS new_deaths_covid19_2020,
		SUM(deaths_covid19_2020) AS deaths_covid19_2020,
		SUM(new_deaths_covid19_2019) AS new_deaths_covid19_2019,
		SUM(deaths_covid19_2019) AS deaths_covid19_2019
	FROM deaths_by_arpen_per_week
	GROUP BY
		epidemiological_week;

DROP VIEW IF EXISTS deaths_by_ses_per_week;
CREATE VIEW deaths_by_ses_per_week AS
	SELECT
		w.epidemiological_week,
		c.state,
		CASE WHEN MAX(c.confirmed) = '' THEN 0 ELSE MAX(c.confirmed) END AS confirmed,
		CASE WHEN MAX(c.deaths) = '' THEN 0 ELSE MAX(c.deaths) END AS deaths
	FROM caso AS c
		LEFT JOIN epidemiological_week AS w
			ON c.date = w.date
	WHERE
		c.place_type = 'state'
	GROUP BY
		w.epidemiological_week,
		c.state
	ORDER BY
		w.epidemiological_week ASC,
		c.state ASC;

DROP VIEW IF EXISTS deaths_brazil_by_ses_per_day;
CREATE VIEW deaths_brazil_by_ses_per_day AS
	SELECT
		c.date,
		SUM(c.confirmed) AS confirmed,
		SUM(c.deaths) AS deaths
	FROM caso AS c
	WHERE
		c.place_type = 'state'
	GROUP BY
		c.date
	ORDER BY
		c.date;
