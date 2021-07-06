DROP MATERIALIZED VIEW IF EXISTS paciente_com_3_ou_mais_aplicacoes;
CREATE MATERIALIZED VIEW paciente_com_3_ou_mais_aplicacoes AS
  SELECT
    paciente_id,
    COUNT(*) AS contagem
  FROM microdados_vacinacao_raw
  GROUP BY paciente_id
  HAVING COUNT(*) >= 3
  ORDER BY COUNT(*) DESC;

DROP MATERIALIZED VIEW IF EXISTS paciente_com_3_ou_mais_aplicacoes_por_estado;
CREATE MATERIALIZED VIEW paciente_com_3_ou_mais_aplicacoes_por_estado AS
  SELECT
    t.paciente_id,
    m.estabelecimento_uf,
    COUNT(*) AS contagem
  FROM paciente_com_3_ou_mais_aplicacoes AS t
    LEFT JOIN microdados_vacinacao_raw AS m
      ON t.paciente_id = m.paciente_id
  GROUP BY
    t.paciente_id,
    m.estabelecimento_uf;

DROP MATERIALIZED VIEW IF EXISTS ufs_diferentes_por_paciente;
CREATE MATERIALIZED VIEW ufs_diferentes_por_paciente AS
  WITH cte AS (
    SELECT
      COUNT(DISTINCT estabelecimento_uf) AS ufs_por_paciente
    FROM microdados_vacinacao_raw
    GROUP BY paciente_id
  )
  SELECT
    ufs_por_paciente,
    COUNT(*) AS contagem
  FROM cte
  GROUP BY ufs_por_paciente;

DROP MATERIALIZED VIEW IF EXISTS paciente_com_numero_dose_incorreto;
CREATE MATERIALIZED VIEW paciente_com_numero_dose_incorreto AS
  SELECT
    estabelecimento_uf,
    COUNT(*) AS contagem
  FROM microdados_limpos
  WHERE
    numero_dose IS NOT NULL
    AND numero_dose NOT IN (1, 2)
  GROUP BY estabelecimento_uf;

DROP MATERIALIZED VIEW IF EXISTS vacina_fabricante;
CREATE MATERIALIZED VIEW vacina_fabricante AS
  SELECT
    vacina_codigo,
    vacina_nome,
    vacina_fabricante_nome,
    vacina_fabricante_referencia,
    COUNT(*) AS contagem
  FROM microdados_vacinacao_raw
  GROUP BY
    vacina_codigo,
    vacina_nome,
    vacina_fabricante_nome,
    vacina_fabricante_referencia;

DROP MATERIALIZED VIEW IF EXISTS atraso_importacao;
CREATE MATERIALIZED VIEW atraso_importacao AS
  SELECT
    estabelecimento_uf,
    COUNT(*) AS contagem,
    SUM(
      DATE_PART(
        'day',
        CAST(data_importacao AS timestamp) - CAST(data_aplicacao AS timestamp)
      )
    ) AS soma_atraso,
    AVG(
      DATE_PART(
        'day',
        CAST(data_importacao AS timestamp) - CAST(data_aplicacao AS timestamp)
      )
    ) AS media_atraso
  FROM microdados_limpos
  WHERE
    data_aplicacao IS NOT NULL
    AND data_importacao IS NOT NULL
    AND CAST(data_aplicacao AS timestamp) > '2021-01-17'::timestamp
  GROUP BY estabelecimento_uf;

DROP MATERIALIZED VIEW IF EXISTS numero_dose_3_ou_mais;
CREATE MATERIALIZED VIEW numero_dose_3_ou_mais AS
  WITH cte AS (
    SELECT
      estabelecimento_uf,
      unnest(array_agg(numero_dose)) AS numero_dose
    FROM microdados_limpos
    GROUP BY paciente_id
    HAVING COUNT(*) >= 3
  )
  SELECT
    numero_dose,
    COUNT(*) AS contagem
  FROM cte
  GROUP BY numero_dose;

DROP MATERIALIZED VIEW IF EXISTS numero_dose_3_ou_mais_por_estado;
CREATE MATERIALIZED VIEW numero_dose_3_ou_mais_por_estado AS
  WITH cte AS (
    SELECT
      unnest(array_agg(estabelecimento_uf)) AS estabelecimento_uf,
      unnest(array_agg(numero_dose)) AS numero_dose
    FROM microdados_limpos
    GROUP BY paciente_id
    HAVING COUNT(*) >= 3
  )
  SELECT
    estabelecimento_uf,
    numero_dose,
    COUNT(*) AS contagem
  FROM cte
  GROUP BY
    estabelecimento_uf,
    numero_dose;

DROP MATERIALIZED VIEW IF EXISTS idade_incorreta;
CREATE MATERIALIZED VIEW idade_incorreta AS
  SELECT
    COUNT(*) AS contagem
  FROM microdados_vacinacao_raw
  WHERE
    date_part('year', age(vacina_dataaplicacao::date, paciente_datanascimento::date)) <> paciente_idade::int;

DROP MATERIALIZED VIEW IF EXISTS grupo_incorreto;
CREATE MATERIALIZED VIEW grupo_incorreto AS
  SELECT
    paciente_id,
    estabelecimento_uf,
    date_part('year', age(vacina_dataaplicacao::date, paciente_datanascimento::date)) AS idade,
    vacina_grupoatendimento_nome
  FROM microdados_vacinacao_raw
  WHERE
    vacina_categoria_nome = 'Faixa Etária'
    AND date_part('year', age(vacina_dataaplicacao::date, paciente_datanascimento::date)) < substring(vacina_grupoatendimento_nome from '\d+')::int;

DROP MATERIALIZED VIEW IF EXISTS somente_segunda_dose_por_estado;
CREATE MATERIALIZED VIEW somente_segunda_dose_por_estado AS
  WITH cte AS (
    SELECT
      unnest(array_agg(estabelecimento_uf)) AS estabelecimento_uf
    FROM microdados_limpos
    GROUP BY paciente_id
    HAVING
      array_agg(DISTINCT numero_dose) = array[2]
  )
  SELECT
    estabelecimento_uf,
    COUNT(*) AS contagem
  FROM cte
  GROUP BY estabelecimento_uf;

DROP MATERIALIZED VIEW IF EXISTS menos_60;
CREATE MATERIALIZED VIEW menos_60 AS
  SELECT
    COUNT(*)
  FROM microdados_vacinacao_raw
  WHERE
    vacina_categoria_nome = 'Faixa Etária'
    AND paciente_idade::int < 60;

DROP MATERIALIZED VIEW paciente_somente_2_doses;
CREATE MATERIALIZED VIEW paciente_somente_2_doses AS
  SELECT
    paciente_id,
    COUNT(*) AS contagem
  FROM microdados_limpos
  GROUP BY paciente_id
  HAVING
    array_agg(DISTINCT numero_dose) = array[2];
