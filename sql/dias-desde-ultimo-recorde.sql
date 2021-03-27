DROP MATERIALIZED VIEW IF EXISTS total CASCADE;
CREATE MATERIALIZED VIEW total AS
	SELECT
		"date",
		SUM(new_confirmed) AS new_confirmed,
		SUM(new_deaths) AS new_deaths
	FROM caso_full
	WHERE
		place_type = 'state'
	GROUP BY "date";
DROP MATERIALIZED VIEW IF EXISTS total_ma7 CASCADE;
CREATE MATERIALIZED VIEW total_ma7 AS
	SELECT
		t."date",
		AVG(t.new_confirmed) OVER (ORDER BY t."date" ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS new_confirmed_ma7,
		AVG(t.new_deaths) OVER (ORDER BY t."date" ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS new_deaths_ma7
	FROM total AS t;

DROP VIEW IF EXISTS death_records CASCADE;
CREATE VIEW death_records AS
	SELECT
		p.*,
		p."date" - p.last_top_date AS days_since_last_record
	FROM (
		SELECT
			t."date",
			t.new_deaths,
			(
				SELECT "date"
				FROM total
				WHERE "date" < t."date"
				ORDER BY new_deaths DESC
				LIMIT 1
			) AS last_top_date,
			(
				SELECT new_deaths
				FROM total
				WHERE "date" < t."date"
				ORDER BY new_deaths DESC
				LIMIT 1
			) AS last_top_new_deaths
		FROM total AS t
	) AS p
	ORDER BY p."date";
DROP VIEW IF EXISTS death_records_ma7 CASCADE;
CREATE VIEW death_records_ma7 AS
	SELECT
		p.*,
		p."date" - p.last_top_date AS days_since_last_record
	FROM (
		SELECT
			t."date",
			t.new_deaths_ma7,
			(
				SELECT "date"
				FROM total_ma7
				WHERE "date" < t."date"
				ORDER BY new_deaths_ma7 DESC
				LIMIT 1
			) AS last_top_date,
			(
				SELECT new_deaths_ma7
				FROM total_ma7
				WHERE "date" < t."date"
				ORDER BY new_deaths_ma7 DESC
				LIMIT 1
			) AS last_top_new_deaths_ma7
		FROM total_ma7 AS t
	) AS p
	ORDER BY p."date";
