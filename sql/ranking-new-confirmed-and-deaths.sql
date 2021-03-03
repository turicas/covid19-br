DROP MATERIALIZED VIEW IF EXISTS caso_total;
CREATE MATERIALIZED VIEW caso_total AS
	SELECT
		date,
		EXTRACT(DOW FROM date) AS day_of_week,
		SUM(new_confirmed) AS new_confirmed,
		SUM(new_deaths) AS new_deaths
	FROM caso_full
	WHERE
		place_type = 'state'
	GROUP BY date;

DROP TABLE IF EXISTS day_name;
CREATE TABLE day_name (day_of_week INTEGER, name TEXT);
INSERT INTO day_name
	VALUES
		(0, 'Domingo'),
		(1, 'Segunda-feira'),
		(2, 'Terça-feira'),
		(3, 'Quarta-feira'),
		(4, 'Quinta-feira'),
		(5, 'Sexta-feira'),
		(6, 'Sábado');

SELECT
	(
		SELECT
			date
		FROM caso_total
		WHERE
			new_confirmed = MAX(t.new_confirmed)
			AND day_of_week = t.day_of_week
	) AS date,
	(SELECT name FROM day_name WHERE day_of_week = t.day_of_week LIMIT 1) AS week_day,
	MAX(new_confirmed) AS new_confirmed
FROM caso_total AS t
GROUP BY day_of_week
ORDER BY day_of_week;

SELECT
	(
		SELECT
			date
		FROM caso_total
		WHERE
			new_deaths = MAX(t.new_deaths)
			AND day_of_week = t.day_of_week
	) AS date,
	(SELECT name FROM day_name WHERE day_of_week = t.day_of_week) AS week_day,
	MAX(new_deaths) AS new_deaths
FROM caso_total AS t
GROUP BY day_of_week
ORDER BY day_of_week;
