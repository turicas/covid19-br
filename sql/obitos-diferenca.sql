SELECT
	n.date AS "Data do óbito",
	n.epidemiological_week,
	CASE WHEN a.deaths = '' THEN 0 ELSE a.deaths END AS 'Mortes por covid19 segundo Secretarias Estaduais de Saúde',
	CASE WHEN n.deaths_covid19 = '' THEN 0 ELSE n.deaths_covid19 END AS 'Mortes por suspeita ou confirmação de covid19 segundo cartórios'
	FROM deaths_brazil_2020_by_arpen_per_day AS n
		LEFT JOIN deaths_brazil_by_ses_per_day AS a
			ON a.date = n.date
	WHERE
		a.deaths > 0
		OR n.deaths_covid19 > 0
	ORDER BY
		a.date;
