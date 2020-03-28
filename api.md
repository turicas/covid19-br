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

> ATENÇÃO: API tem paginação (10.000 registros por página). Você deve
> requisitar a página que está linkada em `next` no resultado.

### Casos

`https://brasil.io/api/dataset/covid19/dados/caso`

Colunas :

- 🔍 `search` (full text search)
- 🔍 `date` (YYY-MM-DD)
- 🔍 `state` (sigla da UF, ex : SP)
- 🔍 `city` (pode estar em branco quando o registro é referente ao estado, pode ser preenchido com `Importados` também)
- 🔍 `place_type` (`city` ou `state`)
- 🔍 `is_last` (`True` ou `False`, diz se esse registro é o mais atual para esse município/estado)
- 🔍 `city_ibge_code` (código IBGE do município ou estado)
- `confirmed`: número de casos confirmados
- `deaths`: número de mortes
- `estimated_population_2019`: população estimada para esse município/estado em 2019, segundo o IBGE
- `confirmed_per_100k_inhabitants`: número de casos confirmados por 100.000 habitantes
- `death_rate`: taxa de mortalidade (mortes / confirmados)

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
      "estimated_population_2019": 407319,
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
      "estimated_population_2019": 881935,
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
      "estimated_population_2019": 4144597,
      "is_last": true,
      "place_type": "state",
      "state": "AM"
    },
...
```

### Boletim

`https://brasil.io/api/dataset/covid19/boletim/data`

Colunas:

- 🔍 `search` (full text search)
- 🔍 `date` (YYY-MM-DD)
- 🔍 `state` (sigla da UF, ex.: SP)
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

### Dicas de uso

- [Preencha o formulário de filtros na página do
  dataset](https://brasil.io/dataset/covid19/caso) e copie/cole a
  querystring (a mesma poderá ser passada para a API);
- Filtre por `is_last=True` para ter os dados mais atuais de cada
  município/estado.
