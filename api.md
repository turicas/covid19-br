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


### Boletim

Colunas:

- 🔍 `search` (full text search)
- 🔍 `date` (YYY-MM-DD)
- 🔍 `state` (2 dígitos)
- `url`: link para o boletim
- `notes`: observações sobre esse boletim

🔍 = colunas que podem ser filtrados via query string na API e na interface.


### Caso

- 🔍 `search` (full text search)
- 🔍 `date` (YYY-MM-DD)
- 🔍 `state` (2 dígitos)
- 🔍 `city` (pode estar em branco quando o registro é referente ao estado, pode ser preenchido com `Importados` também)
- 🔍 `place_type` (`city` ou `state`)
- 🔍 `order` (número que identifica a ordem do registro para este município/estado)
- 🔍 `is_last` (`True` ou `False`, diz se esse registro é o mais atual para esse município/estado)
- 🔍 `city_ibge_code` (código IBGE do município ou estado)
- `confirmed`: número de casos confirmados
- `deaths`: número de mortes
- `estimated_population_2019`: população estimada para esse município/estado em 2019, segundo o IBGE
- `confirmed_per_100k_inhabitants`: número de casos confirmados por 100.000 habitantes
- `death_rate`: taxa de mortalidade (mortes / confirmados)


🔍 = colunas que podem ser filtrados via query string na API e na interface.


### Dicas de uso

- [Preencha o formulário de filtros na página do
  dataset](https://brasil.io/dataset/covid19/caso) e copie/cole a
  querystring (a mesma poderá ser passada para a API);
- Filtre por `is_last=True` para ter os dados mais atuais de cada
  município/estado.
