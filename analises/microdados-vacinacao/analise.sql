-- filename: total_registros.csv
SELECT
  COUNT(*) AS "Total de registros analisados"
FROM microdados_vacinacao_raw;

-- filename: total_paciente_doses.csv
SELECT
  COUNT(*) AS "Total de paciente_ids com 1 ou 2 doses"
FROM paciente_doses;

-- filename: total_paciente_id_3_ou_mais.csv
SELECT
  COUNT(*) AS "paciente_ids (únicos) que aparecem em 3 ou mais registros"
FROM paciente_com_3_ou_mais_aplicacoes;

-- filename: total_registros_3_ou_mais.csv
SELECT
  SUM(contagem) AS "Qtd registros com paciente_ids que possuem 3+ registros cada"
FROM paciente_com_3_ou_mais_aplicacoes;

-- filename: total_3_ou_mais_contagem_2.csv
SELECT
  COUNT(DISTINCT paciente_id) AS "paciente_ids (únicos) que aparecem em 3+ registros (p/ UF)"
FROM paciente_com_3_ou_mais_aplicacoes_por_estado;

-- filename: total_3_ou_mais_por_uf.csv
SELECT
  estabelecimento_uf,
  SUM(contagem) AS "paciente_ids (únicos) que aparecem em 3 ou mais registros"
FROM paciente_com_3_ou_mais_aplicacoes_por_estado
GROUP BY estabelecimento_uf;

-- filename: numero_dose_incorreto.csv
SELECT
  numero_dose,
  contagem AS "Qtd de registros (apenas p/ paciente_id c/ 3+)"
FROM numero_dose_3_ou_mais;

-- filename: numero_dose_incorreto_por_estado.csv
SELECT
  numero_dose,
  estabelecimento_uf,
  contagem AS "Qtd de registros (apenas p/ paciente_id c/ 3+)"
FROM numero_dose_3_ou_mais_por_estado;

-- filename: ufs_diferentes.csv
SELECT
  ufs_por_paciente,
  contagem AS "Pacientes com essa quantidade de UFs diferentes"
FROM ufs_diferentes_por_paciente;

-- filename: numero_dose_errado.csv
SELECT
  estabelecimento_uf,
  contagem AS "Registros com número da dose incorreto"
FROM paciente_com_numero_dose_incorreto;

-- filename: somente_segunda_dose_por_uf.csv
SELECT
  estabelecimento_uf,
  contagem AS "Total de pacientes com apenas a segunda dose (apenas os com 1 ou 2 aplicações)",
  FROM somente_segunda_dose_por_estado;

-- filename: somente_segunda_dose.csv
SELECT
  SUM(contagem) AS "Total (Brasil) de pacientes com apenas a segunda dose (apenas os com 1 ou 2 aplicações)"
FROM somente_segunda_dose_por_estado;

-- filename: vacina_fabricante.csv
SELECT * FROM vacina_fabricante;

-- filename: media_atraso_importacao.csv
SELECT
  SUM(soma_atraso) / SUM(contagem) AS "Média (dias) de atraso de importação (nacional)"
FROM atraso_importacao;

-- filename: media_atraso_importacao_por_estado.csv
SELECT
  estabelecimento_uf,
  media_atraso AS "Média (dias) de atraso de importação"
FROM atraso_importacao;

-- filename: idade_fora_do_grupo.csv
SELECT
  estabelecimento_uf,
  COUNT(*) AS "Registros com idade fora da faixa",
  COUNT(DISTINCT paciente_id) AS "Pacientes com idade fora da faixa",
  AVG(idade - substring(vacina_grupoatendimento_nome from '\d+')::int) AS diferenca_idade
FROM grupo_incorreto
GROUP BY estabelecimento_uf
ORDER BY 4 asc;

-- filename: idade_vs_data_nascimento.csv
SELECT
  contagem AS "Registros com paciente_idade incorreta"
FROM idade_incorreta;
