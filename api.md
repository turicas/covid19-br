# API Dataset covid19 no Brasil.IO

## Licença

Os dados dados convertidos estão sob a licença [Creative Commons Attribution
ShareAlike](https://creativecommons.org/licenses/by-sa/4.0/). Caso utilize os
dados, **cite a fonte original e quem tratou os dados**, como: **Fonte:
Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro Justen
e colaboradores/[Brasil.IO](https://brasil.io/)**. Caso compartilhe os dados,
**utilize a mesma licença**.

## Dados

Depois de coletados e checados os dados ficam disponíveis de 3 formas no
[Brasil.IO](https://brasil.io/):

- [Interface Web](https://brasil.io/dataset/covid19) (feita para humanos)
- [API](https://brasil.io/api/dataset/covid19) (feita para humanos que desenvolvem programas) - [veja a documentação da API](api.md)
- [Download do dataset completo](https://data.brasil.io/dataset/covid19/_meta/list.html)

Caso queira acessar os dados antes de serem publicados (ATENÇÃO: pode ser que
não tenham sido checados), você pode [acessar diretamente as planilhas em que
estamos
trabalhando](https://drive.google.com/open?id=1l3tiwrGEcJEV3gxX0yP-VMRNaE1MLfS2).

Se esse programa e/ou os dados resultantes foram úteis a você ou à sua empresa,
**considere [fazer uma doação ao projeto Brasil.IO](https://brasil.io/doe)**,
que é mantido voluntariamente.

### FAQ SOBRE OS DADOS

**Antes de entrar em contato conosco (estamos sobrecarregados) para tirar
dúvidas sobre os dados, [CONSULTE NOSSO FAQ](faq.md).**

Para mais detalhes [veja a metodologia de coleta de
dados](https://drive.google.com/open?id=1escumcbjS8inzAKvuXOQocMcQ8ZCqbyHU5X5hFrPpn4).

## Documentação da API

> ATENÇÃO: a API possui paginação e por padrão são devolvidos 1.000 registros
> por página. Para capturar todos os dados (de todas as páginas), você precisa
> visitar sempre a página referenciada em `next` no JSON resultante. Caso
> queira alterar o número de registros por página, basta passar o valor através
> da *query string* `page_size` (máximo de 10.000 registros por página).

### `caso`

Essa tabela tem apenas os casos relatados pelos boletins das Secretarias
Estaduais de Saúde e, por isso, não possui valores para todos os municípios e
todas as datas - é nossa "tabela canônica", que reflete o que foi publicado.
Caso você precise dos dados por município por dia completos, veja a tabela
[`caso_full`](#caso_full).

Número de casos confirmados e óbitos por município por dia, segundo as
Secretarias Estaduais de Saúde.

- API: https://brasil.io/api/dataset/covid19/caso/data
- Dados completos para download: https://data.brasil.io/dataset/covid19/caso.csv.gz

Colunas:

- 🔍 `search`: passe algum valor para executar a busca por texto completo, que
  compreende algumas das colunas da tabela.
- 🔍 `date`: data de coleta dos dados no formato YYYY-MM-DD.
- 🔍 `state`: sigla da unidade federativa, exemplo: SP.
- 🔍 `city`: nome do município (pode estar em branco quando o registro é
  referente ao estado, pode ser preenchido com `Importados/Indefinidos`
  também).
- 🔍 `place_type`: tipo de local que esse registro descreve, pode ser `city` ou
  `state`.
- 🔍 `order_for_place`: número que identifica a ordem do registro para este
  local. O registro referente ao primeiro boletim em que esse local aparecer
  será contabilizado como `1` e os demais boletins incrementarão esse valor.
- 🔍 `is_last`: campo pré-computado que diz se esse registro é o mais novo para
  esse local, pode ser `True` ou `False` (caso filtre por esse campo, use
  `is_last=True` ou `is_last=False`, **não use o valor em minúsculas**).
- 🔍 `city_ibge_code`: código IBGE do local.
- `confirmed`: número de casos confirmados.
- `deaths`: número de mortes.
- `estimated_population`: população estimada para esse município/estado em
  2020, [segundo o
  IBGE](https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html?=&t=resultados).
  ([acesse o script que faz o download e conversão dos dados de
  população](https://github.com/turicas/censo-ibge)).
- `estimated_population_2019`: população estimada para esse município/estado em
  2019, [segundo o
  IBGE](https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html?=&t=resultados).
  **ATENÇÃO**: essa coluna possui valores desatualizados, prefira usar a coluna
  `estimated_population`.
- `confirmed_per_100k_inhabitants`: número de casos confirmados por 100.000
  habitantes (baseado em `estimated_population`).
- `death_rate`: taxa de mortalidade (mortes / confirmados).

🔍 = colunas que podem ser filtrados via query string na API e na interface.

#### Exemplos

Recuperando todos os casos :

```shell
curl -X GET https://brasil.io/api/dataset/covid19/caso/data
{
  "count": 2023,
  "next": "https://brasil.io/api/dataset/covid19/caso/data?page=2",
  "previous": null,
  "results": [
    {
      "city": "Rio Branco",
      "city_ibge_code": "1200401",
      "confirmed": 25,
      "confirmed_per_100k_inhabitants": 6.1377,
      "date": "2020-03-27",
      "death_rate": null,
      "deaths": 0,
      "estimated_population": 407319,
      "estimated_population_2019": 413418,
      "is_last": true,
      "place_type": "city",
      "state": "AC"
    },
    {
      "city": null,
      "city_ibge_code": "12",
      "confirmed": 25,
      "confirmed_per_100k_inhabitants": 2.83468,
      "date": "2020-03-27",
      "death_rate": null,
      "deaths": 0,
      "estimated_population": 881935,
      "estimated_population_2019": 894470,
      "is_last": true,
      "place_type": "state",
      "state": "AC"
    },
...
```

Recuperando os dados mais atualizados de Alagoas :

```shell
curl -X GET https://brasil.io/api/dataset/covid19/caso/data?is_last=True&state=AL
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "city": "Maceió",
      "city_ibge_code": "2704302",
      "confirmed": 10,
      "confirmed_per_100k_inhabitants": 0.9814,
      "date": "2020-03-26",
      "death_rate": null,
      "deaths": 0,
      "deaths": 0,
      "estimated_population": 1025360,
      "estimated_population_2019": 1018948,
      "is_last": true,
      "place_type": "city",
      "state": "AL"
    },
    {
      "city": "Porto Real do Colégio",
      "city_ibge_code": "2707503",
      "confirmed": 1,
      "confirmed_per_100k_inhabitants": 4.98355,
      "date": "2020-03-26",
      "death_rate": null,
      "deaths": 0,
      "estimated_population": 20112,
      "estimated_population_2019": 20066,
      "is_last": true,
      "place_type": "city",
      "state": "AL"
    },
    {
      "city": null,
      "city_ibge_code": "27",
      "confirmed": 11,
      "confirmed_per_100k_inhabitants": 0.3296,
      "date": "2020-03-26",
      "death_rate": null,
      "deaths": 0,
      "estimated_population": 3351543,
      "estimated_population_2019": 3337357,
      "is_last": true,
      "place_type": "state",
      "state": "AL"
    }
  ]
}
```

Recuperando apenas os dados acumulados mais recentes dos Estados :

```shell
curl -X GET https://brasil.io/api/dataset/covid19/caso/data?is_last=True&place_type=state
{
  "count": 27,
  "next": null,
  "previous": null,
  "results": [
    {
      "city": null,
      "city_ibge_code": "12",
      "confirmed": 25,
      "confirmed_per_100k_inhabitants": 2.83468,
      "date": "2020-03-27",
      "death_rate": null,
      "deaths": 0,
      "estimated_population": 894470,
      "estimated_population_2019": 881935,
      "is_last": true,
      "place_type": "state",
      "state": "AC"
    },
    {
      "city": null,
      "city_ibge_code": "13",
      "confirmed": 81,
      "confirmed_per_100k_inhabitants": 1.95435,
      "date": "2020-03-27",
      "death_rate": 0.0123,
      "deaths": 1,
      "estimated_population": 4207714,
      "estimated_population_2019": 4144597,
      "is_last": true,
      "place_type": "state",
      "state": "AM"
    },
...
```

### `boletim`

Tabela que lista os boletins publicados pelas Secretarias Estaduais de Saúde.
Pode aparecer mais de um para a mesma data e podem existir dias em que as SES
não publicam boletins.

Links para os boletins das Secretarias Estaduais de Saúde de onde retiramos os
dados de casos confirmados e mortes.

- API: https://brasil.io/api/dataset/covid19/boletim/data
- Dados completos para download: https://data.brasil.io/dataset/covid19/boletim.csv.gz

Colunas:

- 🔍 `search`: passe algum valor para executar a busca por texto completo, que
  compreende algumas das colunas da tabela.
- 🔍 `date`: data do boletim no formato YYYY-MM-DD.
- 🔍 `state`: sigla da unidade federativa, exemplo: SP.
- `url`: link para o boletim
- `notes`: observações sobre esse boletim

🔍 = colunas que podem ser filtrados via query string na API e na interface.

#### Exemplos

Recuperando todos os boletins do estado de São Paulo :

```shell
curl -X GET https://brasil.io/api/dataset/covid19/boletim/data?state=SP
{
  "count": 28,
  "next": null,
  "previous": null,
  "results": [
    {
      "date": "2020-03-26",
      "notes": null,
      "state": "SP",
      "url": "http://www.saude.sp.gov.br/resources/cve-centro-de-vigilancia-epidemiologica/areas-de-vigilancia/doencas-de-transmissao-respiratoria/coronavirus/coronavirus2603_31situacao_epidemiologica.pdf"
    },
    {
      "date": "2020-03-25",
      "notes": "e-mail recebido pelo Turicas",
      "state": "SP",
      "url": "http://www.saude.sp.gov.br/resources/cve-centro-de-vigilancia-epidemiologica/areas-de-vigilancia/doencas-de-transmissao-respiratoria/coronavirus/coronavirus2503_30situacao_epidemiologica.pdf"
    },
    {
      "date": "2020-03-24",
      "notes": null,
      "state": "SP",
      "url": "http://www.portaldenoticias.saude.sp.gov.br/sp-registra-40-obitos-relacionados-a-covid-19/"
    },
...
```


### `caso_full`

Tabela gerada a partir da tabela [`caso`](#caso), que possui um registro por
município (+ Importados/Indefinidos) e estado para cada data disponível; nos
casos em que um boletim não foi divulgado naquele dia, é copiado o dado do
último dia disponível e a coluna `is_repeated` fica com o valor `True`.

- API: https://brasil.io/api/dataset/covid19/caso_full/data
- Dados completos para download: https://data.brasil.io/dataset/covid19/caso_full.csv.gz

Colunas:

- 🔍 `city`: nome do município (pode estar em branco quando o registro é
  referente ao estado, pode ser preenchido com `Importados/Indefinidos`
  também).
- 🔍 `city_ibge_code`: código IBGE do local.
- 🔍 `date`: data de coleta dos dados no formato `YYYY-MM-DD`.
- 🔍 `epidemiological_week`: número da semana epidemiológica no formato `YYYYWW`.
- `estimated_population`: população estimada para esse município/estado em
  2020, [segundo o
  IBGE](https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html?=&t=resultados).
  ([acesse o script que faz o download e conversão dos dados de
  população](https://github.com/turicas/censo-ibge)).
- `estimated_population_2019`: população estimada para esse município/estado em
  2019, [segundo o
  IBGE](https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html?=&t=resultados).
  **ATENÇÃO**: essa coluna possui valores desatualizados, prefira usar a coluna
  `estimated_population`.
- 🔍 `is_last`: campo pré-computado que diz se esse registro é o mais novo para
  esse local, pode ser `True` ou `False` (caso filtre por esse campo, use
  `is_last=True` ou `is_last=False`, **não use o valor em minúsculas**).
- 🔍 `is_repeated`: campo pré-computado que diz se as informações nesse
  registro foram publicadas pela Secretaria Estadual de Saúde no dia `date` ou
  se o dado é repetido do último dia em que o dado está disponível (igual ou
  anterior a `date`). Isso ocorre pois nem todas as secretarias publicam
  boletins todos os dias. Veja também o campo `last_available_date`.
- `last_available_confirmed`: número de casos confirmados do último dia
  disponível igual ou anterior à data `date`.
- `last_available_confirmed_per_100k_inhabitants`: número de casos confirmados
  por 100.000 habitantes (baseado em `estimated_population`) do último dia
  disponível igual ou anterior à data `date`.
- 🔍 `last_available_date`: data da qual o dado se refere.
- `last_available_death_rate`: taxa de mortalidade (mortes / confirmados) do
  último dia disponível igual ou anterior à data `date`.
- `last_available_deaths`: número de mortes do último dia disponível igual ou
  anterior à data `date`.
- 🔍 `order_for_place`: número que identifica a ordem do registro para este
  local. O registro referente ao primeiro boletim em que esse local aparecer
  será contabilizado como `1` e os demais boletins incrementarão esse valor.
- 🔍 `place_type`: tipo de local que esse registro descreve, pode ser `city` ou
  `state`.
- 🔍 `state`: sigla da unidade federativa, exemplo: SP.
- `new_confirmed`: número de novos casos confirmados desde o último dia (note
  que caso `is_repeated` seja `True`, esse valor sempre será `0` e que esse
  valor pode ser negativo caso a SES remaneje os casos desse município para
  outro).
- `new_deaths`: número de novos óbitos desde o último dia (note que caso
  `is_repeated` seja `True`, esse valor sempre será `0` e que esse valor pode
  ser negativo caso a SES remaneje os casos desse município para outro).

🔍 = colunas que podem ser filtrados via query string na API e na interface.


### `obito_cartorio`

Essa tabela contém dados de óbitos registrados nos cartórios e disponíveis no
[Portal da Transparência do Registro
Civil](https://transparencia.registrocivil.org.br/registral-covid).

**DADOS INCOMPLETOS:** os cartórios podem demorar algumas semanas para
consolidar os dados e, portanto, os dados dos 14 últimos dias (pelo menos) são
incompletos e serão atualizados no futuro. Caso queira ter certeza de que está
trabalhando com números finais (ou quase finais), utilize dados anteriores a 30
dias da data de atualização desse dataset.

- API: https://brasil.io/api/dataset/covid19/obito_cartorio/data
- Dados completos para download: https://data.brasil.io/dataset/covid19/obito_cartorio.csv.gz

Colunas:

- 🔍 `date`: Data no formato YYYY-MM-DD
- 🔍 `state`: Sigla da unidade federativa com dois dígitos, exemplo: SP
- 🔍 `epidemiological_week_2019`: Número da semana epidemiológica para essa data em 2019.
- 🔍 `epidemiological_week_2020`: Número da semana epidemiológica para essa data em 2020.
- `deaths_total_2019`: Quantidade de óbitos totais para o estado `state` acumulados no ano de 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `deaths_total_2020`: Quantidade de óbitos totais para o estado `state` acumulados no ano de 2020 (de 1 de janeiro de 2020 a `date`).
- `new_deaths_total_2019`: Quantidade de óbitos totais para o estado `state` ocorridos no dia/mês de `date`, porém em 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `deaths_covid19`: Quantidade de óbitos em decorrência de suspeita ou confirmação de covid19 para o estado `state` acumulados no ano de 2020 (de 1 de janeiro de 2020 a `date`).
- `new_deaths_total_2020`: Quantidade de óbitos totais para o estado `state` ocorridos na data `date` (em 2020).
- `deaths_indeterminate_2019`: Quantidade de óbitos de motivo indeterminado para o estado `state` acumulados no ano de 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `deaths_indeterminate_2020`: Quantidade de óbitos de motivo indeterminado para o estado `state` acumulados no ano de 2020 (de 1 de janeiro de 2020 a `date`).
- `deaths_others_2019`: Quantidade de óbitos em decorrência de outros motivos para o estado `state` acumulados no ano de 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `deaths_others_2020`: Quantidade de óbitos em decorrência de outros motivos para o estado `state` acumulados no ano de 2020 (de 1 de janeiro de 2020 a `date`).
- `deaths_pneumonia_2019`: Quantidade de óbitos em decorrência de pneumonia para o estado `state` acumulados no ano de 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `deaths_pneumonia_2020`: Quantidade de óbitos em decorrência de pneumonia para o estado `state` acumulados no ano de 2020 (de 1 de janeiro de 2020 a `date`).
- `deaths_respiratory_failure_2019`: Quantidade de óbitos em decorrência de insuficiência respiratória para o estado `state` acumulados no ano de 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `deaths_respiratory_failure_2020`: Quantidade de óbitos em decorrência de insuficiência respiratória para o estado `state` acumulados no ano de 2020 (de 1 de janeiro de 2020 a `date`).
- `deaths_sars_2019`: Quantidade de óbitos em decorrência de SRAG para o estado `state` acumulados no ano de 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `deaths_sars_2020`: Quantidade de óbitos em decorrência de SRAG para o estado `state` acumulados no ano de 2020 (de 1 de janeiro de 2020 a `date`).
- `deaths_septicemia_2019`: Quantidade de óbitos em decorrência de septicemia para o estado `state` acumulados no ano de 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `deaths_septicemia_2020`: Quantidade de óbitos em decorrência de septicemia para o estado `state` acumulados no ano de 2020 (de 1 de janeiro de 2020 a `date`).
- `new_deaths_covid19`: Quantidade de óbitos em decorrência de suspeita ou confirmação de covid19 para o estado `state` ocorridos na data `date` (em 2020).
- `new_deaths_indeterminate_2019`: Quantidade de óbitos de motivo indeterminado para o estado `state` ocorridos no dia/mês de `date`, porém em 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `new_deaths_indeterminate_2020`: Quantidade de óbitos de motivo indeterminado para o estado `state` ocorridos na data `date` (em 2020).
- `new_deaths_others_2019`: Quantidade de óbitos em decorrência de outros motivos para o estado `state` ocorridos no dia/mês de `date`, porém em 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `new_deaths_others_2020`: Quantidade de óbitos em decorrência de outros motivos para o estado `state` ocorridos na data `date` (em 2020).
- `new_deaths_pneumonia_2019`: Quantidade de óbitos em decorrência de pneumonia para o estado `state` ocorridos no dia/mês de `date`, porém em 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `new_deaths_pneumonia_2020`: Quantidade de óbitos em decorrência de pneumonia para o estado `state` ocorridos na data `date` (em 2020).
- `new_deaths_respiratory_failure_2019`: Quantidade de óbitos em decorrência de insuficiência respiratória para o estado `state` ocorridos no dia/mês de `date`, porém em 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `new_deaths_respiratory_failure_2020`: Quantidade de óbitos em decorrência de insuficiência respiratória para o estado `state` ocorridos na data `date` (em 2020).
- `new_deaths_sars_2019`: Quantidade de óbitos em decorrência de SRAG para o estado `state` ocorridos no dia/mês de `date`, porém em 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `new_deaths_sars_2020`: Quantidade de óbitos em decorrência de SRAG para o estado `state` ocorridos na data `date` (em 2020).
- `new_deaths_septicemia_2019`: Quantidade de óbitos em decorrência de septicemia para o estado `state` ocorridos no dia/mês de `date`, porém em 2019 (de 1 de janeiro de 2019 a dia/mês de `date` em 2019).
- `new_deaths_septicemia_2020`: Quantidade de óbitos em decorrência de septicemia para o estado `state` ocorridos na data `date` (em 2020).

🔍 = colunas que podem ser filtrados via query string na API e na interface.


### Dicas de uso

- [Preencha o formulário de filtros na página do
  dataset](https://brasil.io/dataset/covid19/caso) e copie/cole a
  querystring (a mesma poderá ser passada para a API);
- Em `caso` filtre por `is_last=True` para ter os dados mais atuais de cada
  município/estado;
- Em `caso_full` filtre por `had_cases=True` para ter dados apenas a partir das
  datas em que os locais começaram a reportar o número de casos maior que 1.
