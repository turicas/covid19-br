SELECT
	*,
	(confirmed_state - confirmed_cities) AS confirmed_diff,
	(deaths_state - deaths_cities) AS deaths_diff
FROM total_from_state_and_cities
WHERE
	confirmed_diff != 0
	OR deaths_diff != 0;
