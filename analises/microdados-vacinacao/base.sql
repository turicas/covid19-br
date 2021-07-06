-- Cria índices para agilizar consultas posteriores
CREATE INDEX IF NOT EXISTS idx_microdados_raw_paciente ON microdados_vacinacao_raw (
  paciente_id,
  estabelecimento_uf
);
CREATE INDEX IF NOT EXISTS idx_microdados_raw_datas ON microdados_vacinacao_raw (
  data_importacao_rnds,
  vacina_dataaplicacao,
  estabelecimento_uf
);


-- Cria tipo ENUM para guardar nomes das vacinas (filtros ficam mais rápidos)
CREATE TYPE vacina_enum AS ENUM ('ad26cov2s', 'bnt162b2', 'coronavac', 'covishield');


-- Cria vista com dados convertidos para um formato que facilitará as próximas
-- consultas, apenas com as colunas necessárias
DROP VIEW IF EXISTS microdados_limpos CASCADE;
CREATE VIEW microdados_limpos AS
  SELECT
    substring(data_importacao_rnds from 1 for 10) AS data_importacao,
    ('\x' || paciente_id)::bytea AS paciente_id,
    vacina_dataaplicacao::date AS data_aplicacao,
    CASE
      WHEN substring(vacina_descricao_dose from '\d') IS NOT NULL THEN
        substring(vacina_descricao_dose from '\d')::int
      WHEN substring(vacina_descricao_dose from 'Única') IS NOT NULL THEN
        1
      ELSE NULL
    END AS numero_dose,
    estabelecimento_uf,
    (CASE
      WHEN vacina_nome = 'Covid-19-AstraZeneca' THEN 'covishield'
      WHEN vacina_nome = 'Covid-19-Coronavac-Sinovac/Butantan' THEN 'coronavac'
      WHEN vacina_nome = 'Pendente Identificação' THEN NULL
      WHEN vacina_nome = 'Vacina Covid-19 - Covishield' THEN 'covishield'
      WHEN vacina_nome = 'Vacina covid-19 - Ad26.COV2.S - Janssen-Cilag' THEN 'ad26cov2s'
      WHEN vacina_nome = 'Vacina covid-19 - BNT162b2 - BioNTech/Fosun Pharma/Pfizer' THEN 'bnt162b2'
      ELSE vacina_nome
    END)::vacina_enum AS vacina
  FROM
    microdados_vacinacao_raw;


-- Cria vista materializada (será bastante utilizada nas consultas), agrupando
-- por paciente_id e preenchendo as datas da primeira e segunda doses, nome da
-- vacina e UF do estabelecimento de saúde no mesmo registro. Não inclui
-- pacientes cujos IDs apareçam 3 ou mais vezes na tabela original.
CREATE MATERIALIZED VIEW paciente_doses AS
  SELECT
    paciente_id,
    min(data_aplicacao) FILTER (WHERE (numero_dose = 1 OR numero_dose IS NULL) AND data_aplicacao IS NOT NULL) AS data_aplicacao_primeira_dose,
    max(data_aplicacao) FILTER (WHERE numero_dose = 2 AND data_aplicacao IS NOT NULL) AS data_aplicacao_segunda_dose,
    (max(data_aplicacao) FILTER (WHERE numero_dose = 2 AND data_aplicacao IS NOT NULL)) -
      (min(data_aplicacao) FILTER (WHERE (numero_dose = 1 OR numero_dose IS NULL) AND data_aplicacao IS NOT NULL)) AS dias_entre_doses,
    CASE
      WHEN min(estabelecimento_uf) FILTER (WHERE (numero_dose = 1 OR numero_dose IS NULL) AND estabelecimento_uf IS NOT NULL) IS NOT NULL
        THEN min(estabelecimento_uf) FILTER (WHERE (numero_dose = 1 OR numero_dose IS NULL) AND estabelecimento_uf IS NOT NULL)
        ELSE min(estabelecimento_uf) FILTER (WHERE numero_dose = 2 AND estabelecimento_uf IS NOT NULL)
    END AS estabelecimento_uf,
    CASE
      WHEN min(vacina) FILTER (WHERE (numero_dose = 1 OR numero_dose IS NULL) AND vacina IS NOT NULL) IS NOT NULL
        THEN min(vacina) FILTER (WHERE (numero_dose = 1 OR numero_dose IS NULL) AND vacina IS NOT NULL)
        ELSE min(vacina) FILTER (WHERE numero_dose = 2 AND vacina IS NOT NULL)
    END AS vacina
  FROM
    microdados_limpos
  GROUP BY
      paciente_id
  HAVING COUNT(*) < 3;


-- Cria índices na view materializada para agilizar pŕoximas consultas de
-- agregração
CREATE INDEX idx_paciente_doses_diferenca ON paciente_doses (
  dias_entre_doses,
  estabelecimento_uf
);
CREATE INDEX idx_paciente_doses_data_aplicacao_primeira_dose ON paciente_doses (
  data_aplicacao_primeira_dose,
  data_aplicacao_segunda_dose,
  vacina
);
CREATE INDEX idx_paciente_doses_dias_entre_doses_uf ON paciente_doses (
  dias_entre_doses,
  estabelecimento_uf
);
CREATE INDEX idx_paciente_doses_filter ON paciente_doses (
  vacina,
  data_aplicacao_primeira_dose,
  dias_entre_doses
);


CREATE VIEW microdados_limpos2 AS
  SELECT
    substring(data_importacao_rnds from 1 for 10) AS data_importacao,
    paciente_id,
    vacina_dataaplicacao::date AS data_aplicacao,
    CASE
      WHEN substring(vacina_descricao_dose from '\d') IS NOT NULL THEN
        substring(vacina_descricao_dose from '\d')::int
      WHEN substring(vacina_descricao_dose from 'Única') IS NOT NULL THEN
        1
      ELSE NULL
    END AS numero_dose,
    estabelecimento_uf,
    (CASE
      WHEN vacina_nome = 'Covid-19-AstraZeneca' THEN 'covishield'
      WHEN vacina_nome = 'Covid-19-Coronavac-Sinovac/Butantan' THEN 'coronavac'
      WHEN vacina_nome = 'Pendente Identificação' THEN NULL
      WHEN vacina_nome = 'Vacina Covid-19 - Covishield' THEN 'covishield'
      WHEN vacina_nome = 'Vacina covid-19 - Ad26.COV2.S - Janssen-Cilag' THEN 'ad26cov2s'
      WHEN vacina_nome = 'Vacina covid-19 - BNT162b2 - BioNTech/Fosun Pharma/Pfizer' THEN 'bnt162b2'
      ELSE vacina_nome
    END)::vacina_enum AS vacina
  FROM
    microdados_vacinacao_raw;
