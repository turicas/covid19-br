SELECT
	c.*
FROM caso AS c
	INNER JOIN ultimas_atualizacoes AS l
	ON
		c.date = l.last_date
		AND c.state = l.state
		AND c.city = l.city
		AND c.place_type = l.place_type
		AND c.order_for_place = l.last_order_for_place;
