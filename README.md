[🇺🇸 English?](README.en.md)

# covid19-br

![pytest@docker](https://github.com/turicas/covid19-br/workflows/pytest@docker/badge.svg) ![goodtables](https://github.com/turicas/covid19-br/workflows/goodtables/badge.svg)

Esse repositório centraliza links e dados sobre boletins de número de casos das
Secretarias Estaduais de Saúde (SES) sobre os casos de covid19 no Brasil (por
município por dia), além de outros dados relevantes para a análise, como óbitos
registrados em cartório (por estado por dia).


## Tabela de Conteúdos
1. [Licença e Citação](#licena-e-citao)
2. [Sobre os dados](#dados)
3. [Guia de contribuição geral](#contribuindo)
4. [Guia de instalação / setup do projeto (ambiente de desenvolvimento)](#instalando)
5. [Guia de como executar os scrapers existentes](#executando-os-scrapers)
6. [Guia de como criar novos scrapers](#criando-novos-scrapers)
7. [Guia de como atualizar os dados no Brasil.io (ambiente de produção)](#atualizao-dos-dados-no-brasilio)

## Licença e Citação

A licença do código é [LGPL3](https://www.gnu.org/licenses/lgpl-3.0.en.html) e
dos dados convertidos [Creative Commons Attribution
ShareAlike](https://creativecommons.org/licenses/by-sa/4.0/). Caso utilize os
dados, **cite a fonte original e quem tratou os dados** e caso compartilhe os
dados, **utilize a mesma licença**.
Exemplos de como os dados podem ser citados:
- **Fonte: Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro Justen e equipe de voluntários [Brasil.IO](https://brasil.io/)**
- **Brasil.IO: boletins epidemiológicos da COVID-19 por município por dia, disponível em: https://brasil.io/dataset/covid19/ (última atualização pode ser conferida no site).**


## Dados

Depois de coletados e checados os dados ficam disponíveis de 3 formas no
[Brasil.IO](https://brasil.io/):

- [Interface Web](https://brasil.io/dataset/covid19) (feita para humanos)
- [API](https://brasil.io/api/dataset/covid19) (feita para humanos que desenvolvem programas) - [veja a documentação da API](api.md)
- [Download do dataset completo](https://data.brasil.io/dataset/covid19/_meta/list.html)

Caso queira acessar os dados antes de serem publicados (ATENÇÃO: pode ser que
não tenham sido checados), você pode [acessar diretamente as planilhas em que
estamos trabalhando](https://drive.google.com/open?id=1l3tiwrGEcJEV3gxX0yP-VMRNaE1MLfS2).

Se esse programa e/ou os dados resultantes foram úteis a você ou à sua empresa,
**considere [fazer uma doação ao projeto Brasil.IO](https://brasil.io/doe)**,
que é mantido voluntariamente.


### FAQ SOBRE OS DADOS

**Antes de entrar em contato conosco (estamos sobrecarregados) para tirar
dúvidas sobre os dados, [CONSULTE NOSSO FAQ](faq.md).**

Para mais detalhes [veja a metodologia de coleta de
dados](https://drive.google.com/open?id=1escumcbjS8inzAKvuXOQocMcQ8ZCqbyHU5X5hFrPpn4).


### Clipping

Quer saber quais projetos e notícias estão usando nossos dados? [Veja o
clipping](clipping.md).


### Analisando os dados

Caso queira analisar os dados usando SQL, veja o script
[`analysis.sh`](analysis.sh) (ele baixa e converte os CSVs para um banco de
dados SQLite e já cria índices e *views* que facilitam o trabalho) e os
arquivos na pasta [`sql/`](sql/).

Por padrão o script reutiliza os arquivos
caso já tenha baixado; para sempre baixar a versão mais atual dos dados,
execute `./analysis.sh --clean`.

Leia também nossa [análise dos microdados de vacinação disponíveis no
OpenDataSUS](analises/microdados-vacinacao/README.md).


### Validando os dados

Os metadados estão descritos conforme os padrões *Data Package* e
*[Table Schema](https://specs.frictionlessdata.io/table-schema/#language)* do
*[Frictionless Data](https://frictionlessdata.io/)*. Isso significa que os
dados podem ser validados automaticamente para detectar, por exemplo, se os
valores de um campo estão em conformidade com a tipagem definida, se uma data
é válida, se há colunas faltando ou se há linhas duplicadas.

Para fazer a verificação, ative o ambiente virtual Python e em seguida digite:

```
goodtables data/datapackage.json
```

O relatório da ferramenta
*[Good Tables](https://github.com/frictionlessdata/goodtables-py)* irá indicar
se houver alguma inconsistência. A validação também pode ser feita *online*
pelo site [Goodtables.io](http://goodtables.io/).


### Mais informações

Você pode ter interesse em ver também:
- [Outros datasets relevantes](datasets-relevantes.md)
- [Recomendações para secretarias de saúde na disponibilização de
  dados](recomendacoes.md)


## Contribuindo

Você pode contribuir de diversas formas:

- Criando programas (crawlers/scrapers/spiders) para extrair os dados automaticamente ([LEIA ESSE GUIA ANTES](#criando-novos-scrapers));
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


## Instalando

Este projeto utiliza Python 3 (testado em 3.8.2) e Scrapy.

Você pode montar seu ambiente de desenvolvimento utilizando o
[setup padrão](#setup-padro) ou o [setup com docker](#setup-com-docker).

### Setup Padrão

1. Instale o Python 3.8.2
2. Crie um virtualenv (você pode usar
  [venv](https://docs.python.org/pt-br/3/library/venv.html) para isso).
3. Instale as dependências: `pip install -r requirements-development.txt`


### Setup com Docker

Se você preferir utilizar o Docker para executar, basta usar os comandos a seguir :

```shell
make docker-build       # para construir a imagem
make docker-run-spiders # para coletar os dados
```

## Executando os scrapers

Uma vez que seu [setup](#instalando) estiver terminado, você pode rodar **todos os
scrapers** usando um dos seguintes comandos no seu terminal (a depender do tipo de
setup que decidiu fazer):

```shell
python covid19br/run_spider.py  # caso tenha feito o setup padrão
make docker-run-spiders         # caso esteja usando o setup com docker
```

Os comandos acima irão rodar os scrapers de **todos os estados** que temos implementado
buscando os dados sobre a **data de hoje** e **salvarão o consolidado** em `.csv` na pasta
`data` deste diretório (por padrão são salvos em arquivos com o nome no padrão 
`"data/{estado}/covid19-{estado}-{data}{extra_info}.csv"`).

Mas essa não é a única forma de usar esse comando, você pode optar por não salvar os
consolidados em um `.csv` (apenas exibi-los na tela) ou então rodar apenas os scrapers
de alguns estados específicos ou para outros dias específicos que não são necessariamente
a data de hoje.

Para adaptar melhor o comando ao seu caso de uso você pode rodá-lo no terminal com
as seguintes opções:

> OBS: Se você estiver usando docker, basta acrescentar `docker container run --rm
 --name covid19-br -v $(PWD)/data:/app/data covid19-br` antes de qualquer um dos
  comandos a seguir.

```shell
# Exemplo de como raspar os dados de todos os estados em um intervalo de datas
python covid19br/run_spider.py --start_date 24/02/2021 --end_date 30/03/2021

# Caso você queira executar para datas específicas (coloque-as em lista separando-as por vírgulas):
python covid19br/run_spider.py --dates_range  15/01/2022,17/01/2022

# Para executar apenas spiders de estados específicos (coloque-os em lista e separados por vírgulas):
python covid19br/run_spider.py --states BA,PR

# Para ver quais são os estados com scrapers implementados:
python covid19br/run_spider.py --available_spiders

# Caso você não queira salvar os csv's, apenas mostrar na tela os resultados:
python covid19br/run_spider.py --print_results_only

# Você pode consultar essas e outras opções disponíveis usando:
python covid19br/run_spider.py -h
```

## Criando novos scrapers

Estamos mudando a forma como subimos os dados para facilitar o trabalho dos
voluntários e deixar o processo mais robusto e confiável e, com isso, será
mais fácil que robôs possam subir também os dados; dessa forma, os scrapers
ajudarão *bastante* no processo.

Porém, ao criar um scraper é importante que você siga algumas regras:

- **Necessário** fazer o scraper usando o `scrapy` (confira [aqui as docs](https://scrapy.org/));
- **Não usar** `pandas`, `BeautifulSoap`, `requests` ou outras bibliotecas
  desnecessárias (a std lib do Python já tem muita biblioteca útil, o `scrapy`
  com XPath já dá conta de boa parte das raspagens e `rows` já é uma dependência
  desse repositório);

Para padronizar a forma que os scrapers recebem parâmetros e retornam os dados,
criamos um [Spider Base](covid19br/common/base_spider.py), que nada mais é que
um spider básico do scrapy com lógica a mais para:
- Identificar _para quais datas_ o spider deve procurar dados (essa informação
  é recebida como parâmetro e é guardada na classe no atributo `self.dates_range`,
  que é um `generator` de valores do tipo `datetime.date` com as datas que precisamos
  raspar os dados, e deve ser usada pelo seu spider para buscar os dados como
  solicitado).
- Guardar os dados raspados de uma forma que sejam retornados para o
  sistema que chamou o scraper de forma padronizada.

Para padronizar os dados que são retornados pelos spiders, criamos a classe
[FullReport](covid19br/common/models/full_report.py) que representa um "relatório
completo" e armazena todos os dados coletados para um determinado estado em uma
data específica. Esse relatório completo é composto por vários [boletins](covid19br/common/models/bulletin_models.py),
(um para cada cidade do estado + um para casos importados/indefinidos) com o
número de casos confirmados e número de mortes daquele dia.

O seu script não precisa se preocupar com a criação do objeto `FullReport` que será
retornado, isso é responsabilidade do [Spider Base](covid19br/common/base_spider.py),
o que seu spider deve criar são os [boletins](covid19br/common/models/bulletin_models.py)
com os dados que ele coletar e salvar esses `boletins` no relatório através do método
`add_new_bulletin_to_report` disponibilizado pelo `Spider Base`.

Em resumo, ao criar um spider de um novo estado tenha em mente:
- É desejável que você crie seu spider extendendo a classe [Spider Base](covid19br/common/base_spider.py)
  (você pode conferir alguns exemplos de como outros spiders são implementados na pasta
  [/covid19br/spiders](covid19br/spiders)).
- Um spider completo é capaz de coletar os dados:
    - De número de casos confirmados e número de mortes **por cidade** do estado;
    - De número de casos confirmados e número de mortes **importados/indefinidos**;
    - De números de casos confirmados e números de mortes **totais** do estado (esse
      valor normalmente é computado automaticamente conforme os casos acimas são obtidos,
      mas em casos onde a scretaria disponibiliza o valor total, nós optamos por usá-lo
      como "fonte da verdade").
    - Para diferentes datas (desde o início da pandemia até hoje).
    > OBS: Como não há uma padronização na forma em que as secretarias disponibilizam os
    dados, nem sempre é possível obter todas essas informações como desejamos. Obter parte
    dessas informações de forma automatizada já pode ser um bom começo e uma contribuição válida! :)
- Os dados coletados devem ser salvos em [boletins](covid19br/common/models/bulletin_models.py)
  e adicionados no retorno do spider através do método `add_new_bulletin_to_report`.

Ao finalizar a implementação do seu spider, adicione-o na lista de spiders do script
[run_spider.py](covid19br/run_spider.py) e execute-o (mais informações sobre como fazer
isso na seção anterior). Se tudo correu como previsto, é esperado que seja criado um `.csv`
na pasta `/data/...` com os dados raspados pelo seu spider :)

Nesse momento não temos muito tempo disponível para revisão, então **por favor**,
só crie um *pull request* com código de um novo scraper caso você possa cumprir os
requisitos acima.


## Atualização dos Dados no Brasil.IO

Crie um arquivo `.env` com os valores corretos para as seguintes variáveis de
ambiente:

```shell
BRASILIO_SSH_USER
BRASILIO_SSH_SERVER
BRASILIO_DATA_PATH
BRASILIO_UPDATE_COMMAND
BULLETIN_SPREADSHEET_ID
```

Execute o script:

`./deploy.sh full`

Ele irá coletar os dados das planilhas (que estão linkadas em
`data/boletim_url.csv` e `data/caso_url.csv`), adicionar os dados ao
repositório, compactá-los, enviá-los ao servidor e executar o comando de
atualização de dataset.

> Nota: o script que baixa e converte os dados automaticamente deve ser
> executado separadamente, com o comando `./run-spiders.sh`.
