# covid19-br

Esse repositório centraliza links e dados sobre boletins de número de casos das
secretarias de saúde estaduais sobre a pandemia de coronavírus no Brasil. O
recorte é por município por dia, para acompanharmos localmente a evolução da
propagação do vírus.

## Licença

A licença do código é [LGPL3](https://www.gnu.org/licenses/lgpl-3.0.en.html) e
dos dados convertidos [Creative Commons Attribution
ShareAlike](https://creativecommons.org/licenses/by-sa/4.0/). Caso utilize os
dados, **cite a fonte original e quem tratou os dados**, como: **Fonte:
Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro
Justen/[Brasil.IO](https://brasil.io/)**. Caso compartilhe os dados, **utilize
a mesma licença**.

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


## Contribuindo

Você pode contribuir de diversas formas:

- Criando programas (crawlers/scrapers/spiders) para extrair os dados automaticamente ([LEIA ISSO ANTES](#criando-scrapers));
- Coletando links para os boletins de seu estado;
- Coletando dados sobre os casos por município por dia;
- Entrando em contato com a secretaria estadual de seu estado, sugerindo as
  [recomendações de liberação dos dados](recomendacoes.md);
- Evitando contato com humanos;
- Lavando as mãos várias vezes ao dia;
- Sendo solidário aos mais vulneráveis;

Para se voluntariar, [siga estes passos](CONTRIBUTING.md).

Procure o seu estado [nas issues desse
repositório](https://github.com/turicas/covid19-br/issues) e vamos conversar
por lá.

### Criando Scrapers

Estamos mudando a forma de subida dos dados para facilitar o trabalho dos voluntários e deixar o processo mais robusto e confiável e, com isso, será mais fácil que robôs possam subir também os dados; dessa forma, os scrapers ajudarão *bastante* no processo. Porém, ao criar um scraper é importante que você siga algumas regras:

- **Necessário** fazer o scraper usando o `scrapy`;
- **Não usar** `pandas`, `BeautifulSoap`, `requests` ou outras bibliotecas desnecessárias (a std lib do Python já tem muita biblioteca útil, o `scrapy` com XPath já dá conta de boa parte das raspagens e `rows` já é uma dependência desse repositório);
- Deve existir alguma maneira fácil de fazer o scraper coletar os boletins e casos para uma data específica (mas ele deve ser capaz de identificar para quais datas os dados disponíveis e de capturar várias datas também);
- O método de parsing deve devolver (com `yield`) um dicionário com as seguintes chaves:
  - `date`: data no formato `"YYYY-MM-DD"`
  - `state`: sigla do estado, com 2 caracteres maiúsculos (deve ser um atributo da classe do spider e usar `self.state`)
  - `city` (nome do município ou em branco, caso seja o valor do estado, deve ser `None`)
  - `place_type`: `"city"` para município e `"state"` para estado
  - `confirmed`: inteiro, número de casos confirmados (ou `None`)
  - `deaths`: inteiro, número de mortes naquele dia (ou `None`)
  - **ATENÇÃO**: o scraper deve devolver sempre um registro para o estado que *não seja* a soma dos valores por município (esse dado deve ser extraído da linha "total no estado" no boletim) - essa linha virá com a coluna `city` com o valor `None` e `place_type` com `"state"` - esse dado apenas deve vir preenchido como sendo a soma dos valores municipais *caso o boletim não tenha os dados totais*;
- Quando possível, use testes automatizados.

Nesse momento não temos muito tempo disponível para revisão, então **por favor**, só crie um *pull request* com código de um novo scraper caso você possa cumprir os requisitos acima.

## Instalando

Necessita de Python 3 (testado em 3.8.2). Para montar seu ambiente:

- Instale o Python 3.8.2
- Crie um virtualenv
- Instale as dependências:
  - Script de consolidação e robô: `pip install -r requirements.txt`
  - Extratores de dados estaduais: `pip install -r requirements-collect.txt`
- Rode o script de coleta: `./collect.sh`
- Rode o script de consolidação: `./run.sh`

Verifique o resultado em `data/output`.

## VEJA TAMBÉM

- [Outros datasets relevantes](datasets-relevantes.md)
- [Recomendações para secretarias de saúde na disponibilização de
  dados](recomendacoes.md)

## Clipping

Outros projetos e/ou notícias na rede que referenciam este projeto.

### Análises e Projetos

- [25/03/2020 - Análise Descritiva do Coronavírus nos Estados Brasileiros](https://marcusnunes.me/posts/analise-descritiva-do-coronavirus/)
- [Visualização em Mapa Interativo](https://endoedgar.github.io/covid19-monitorbr/) por [@endoedgar](https://github.com/endoedgar)
- [liibre/coronabr](https://liibre.github.io/coronabr/index.html)
- [Observatório de Dados :: COVID-19 no Brasil CCSL-UFPA](http://ccsl.ufpa.br/covid-19/)
- [Mapa do Covid-19 no Brasil](https://covid19.hitalos.com) por [@hitalos](https://github.com/hitalos)
- [Estimativas de R0 por Estados do Brasil](https://flaviovdf.github.io/covid19/) por [@flaviovdf](https://github.com/flaviovdf)
- [Instituto de Comunicação e Informação Científica e Tecnológica em Saúde (Icict/Fiocruz)](https://bigdata-covid19.icict.fiocruz.br/)
- [Dashboard do Brasil sobre Covid-19](https://gabrielcesar.github.io/covid-br/) por [@gabrielcesar](https://github.com/gabrielcesar)


### Notícias

- [31/03/2020 - UFPA - Centro de Competência em Software Livre da UFPA disponibiliza página para acompanhar a evolução da pandemia da Covid-19 no Brasil](https://portal.ufpa.br/index.php/ultimas-noticias2/11475-centro-de-competencia-em-software-livre-da-ufpa-disponibiliza-pagina-para-acompanhar-a-evolucao-da-pandemia-da-covid-19-no-brasil)
- [30/03/2020 - UFRGS - Pesquisadores da UFRGS criam sites para acompanhamento de número de casos de Covid-19 nos municípios](https://www.ufrgs.br/coronavirus/base/pesquisadores-da-ufrgs-criam-sites-para-acompanhamento-de-casos-de-covid-19-nos-municipios/)
- [25/03/2020 - Folha de São Paulo - Brasil tem ao menos 172 cidades com casos confirmados de coronavírus](https://www1.folha.uol.com.br/cotidiano/2020/03/brasil-tem-ao-menos-172-cidades-com-casos-confirmados-de-coronavirus.shtml)
- [24/03/2020 - Metrópole - Covid-19: Ministério da Saúde divulga menos casos que secretarias](https://www.metropoles.com/brasil/saude-br/covid-19-ministerio-da-saude-divulga-menos-casos-que-secretarias)
- [23/03/2020 - CNN Brasil - Boletins estaduais indicam quase 40 casos de coronavírus a mais do que governo](https://www.cnnbrasil.com.br/saude/2020/03/23/boletins-estaduais-indicam-quase-40-casos-de-coronavirus-a-mais-do-que-governo)

## Atualização dos Dados no Brasil.IO

Crie um arquivo `.env` com os valores corretos para as seguintes variáveis de
ambiente:

```shell
BRASILIO_SSH_USER
BRASILIO_SSH_SERVER
BRASILIO_DATA_PATH
BRASILIO_UPDATE_COMMAND
```

Execute o script:

`./deploy.sh`

Ele irá coletar os dados das planilhas (que estão linkadas em
`data/boletim_url.csv` e `data/caso_url.csv`), adicionar os dados ao
repositório, compactá-los, enviá-los ao servidor e executar o comando de
atualização de dataset.

> Nota: o script que baixa e converte os dados automaticamente deve ser
> executado separadamente, com o comando `./collect.sh`.
