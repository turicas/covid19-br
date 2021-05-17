# Análise dos Microdados de Vacinação

Nessa pasta estão os códigos SQL, a descrição da metodologia e perguntas feitas
ao Ministério da Saúde via pedido de acesso à informação com relação aos
[microdados de vacinação disponíveis no
OpenDataSUS](https://opendatasus.saude.gov.br/dataset/covid-19-vacinacao).


## Metodologia

- Baixar CSV (dados completos, nível nacional) diretamente do OpenDataSUS;
- Importar CSV no PostgreSQL (todas as colunas como texto, para agilizar
  processo);
- Rodar consultas em [`base.sql`](base.sql) para criar índices, tipos e vistas
  auxiliares;
- Rodar consultas em [`pre-select.sql`](pre-select.sql) para criar vistas
  materializadas que facilitarão a criação dos relatórios nos passos
  posteriores, preservando os dados para novas análises futuras;
- Rodar consultas em [`analise.sql`](analise.sql) para coletar os
  erros/inconsistências identificados na base (essa ação é feita através do
  script `consultas.py`).


## Pedido de Acesso à Informação

- Órgão destinatário: MS - Ministério da Saúde
- Assunto Coronavírus (COVID-19)
- Resumo: Inconsistências nos microdados de vacinação disponíveis no OpenDataSUS

Considerando os microdados de vacinação a nível nacional (dados completos em
CSV) disponibilizados no OpenDataSUS no dia 14 de maio de 2021, gostaria de
sanar as dúvidas listadas abaixo (após as perguntas, envio alguns exemplos de
dados que comprovam as inconsistências).

1. Qual algoritmo de hashing foi utilizado para gerar a coluna `paciente_id`?
2. A coluna `paciente_id` é gerada pelos municípios, pelos Estados ou pelo
   próprio Ministério?
3. Quais dados do paciente são utilizados (como CPF, CNS etc.) para compor o
   valor final de `paciente_id`?
4. Calculei a média de atraso de importação dos dados a partir da diferença
   entre as colunas `data_importacao_rnds` e `data_aplicacao`. Existe um atraso
   de importação médio nacional de 5.23 dias. A nível estadual, DF, RR, RJ e MS
   possuem as maiores médias (mais de 10 dias). Quais são os prazos que os
   municípios/Estados têm após a aplicação da dose para registrá-la no sistema
   federal e para que o Ministério publique os dados após receber o registro
   desses entes federativos?
5. Existem 467.985 `paciente_id` únicos que possuem 3 ou mais registros
   (totalizando 1.492.626 registros), o que não deveria ocorrer pois as vacinas
   são administradas no máximo em duas doses. O que explica esse erro? Pode ser
   indício de fraude? O que o Ministério está fazendo para investigar o
   problema e corrigi-lo?
6. Para todo o Brasil, existem 659.878 `paciente_id` que possuem apenas a
   segunda dose registrada (no total, são 671.417 registros) e para o estado de
   MG existem 174 registros com o valor para `vacina_descricao_dose` como
   "3ª Dose" ou apenas "Dose". O que explica isso e quando será resolvido?
7. As colunas `vacina_codigo`, `vacina_nome`, `vacina_fabricante_nome` e
   `vacina_fabricante_referencia` possuem valores conflitantes, como códigos
   diferentes para a mesma vacina e nomenclatura diferente para mesmos
   fabricantes. No total, essas 4 colunas geram uma combinação de 199 valores
   distintos, enquanto o esperado seria bem menos (no máximo, o total de
   vacinas vezes o total de fabricantes). O que justifica essa inconsistência?
   Qual é o prazo previsto para normalização desses valores?
8. Existem 170.129 registros de doses aplicadas em indivíduos classificados
   como grupo prioritário "Faixa Etária" na coluna `vacina_categoria_nome`, mas
   que referem-se a pessoas com menos de 60 anos (pela coluna `paciente_idade`)
   e que, portanto, não fariam parte do citado grupo prioritário (idosos) .
   Como o Ministério garante que não há desvio de doses para indivíduos que não
   são do grupo prioritário?

> **Nota 1**: a metodologia e consultas executadas na análise são software livre e
> podem ser consultadas em:
> https://github.com/turicas/covid19-br/tree/master/analises/microdados-vacinacao/README.md

> **Nota 2**: estão anexados arquivos com amostras dos dados que exemplificam
> as questões levantadas ([`pergunta4.csv`](pergunta4.csv),
> [`pergunta5.csv`](pergunta5.csv),
> [`pergunta6-1.csv`](pergunta6-1.csv), [`pergunta6-2.csv`](pergunta6-2.csv),
> [`pergunta7.csv`](pergunta7.csv) e [`pergunta8.csv`](pergunta8.csv)).
