
[🇺🇸 English?](README.en.md)

# covid19-br

![pytest@docker](https://github.com/turicas/covid19-br/workflows/pytest@docker/badge.svg)

<!-- TABLE OF CONTENTS -->
## Tabela de Conteúdo

* [Sobre este Projeto](#sobre-este-projeto)
  * [Feito com](#feito-com)
* [Iniciando](#iniciando)
  * [Pre-requisitos](#pre-requisitos)
  * [Instalação](#instalação)
* [Utilização](#utilização)
* [Roadmap](#roadmap)
* [Contribuindo](#contribuindo)
* [Licença e Citação](#licença-e-citação)
* [Contato](#contato)
* [Agradecimentos](#agradecimentos)



<!-- ABOUT THE PROJECT -->
## Sobre este Projeto

Esse repositório centraliza links e dados sobre boletins de número de casos das
Secretarias Estaduais de Saúde (SES) sobre os casos de covid19 no Brasil (por
município por dia), além de outros dados relevantes para a análise, como óbitos
registrados em cartório (por estado por dia).

### Feito com

* [Python](https://www.python.org/)
* [Bash](https://www.gnu.org/software/bash/)


<!-- GETTING STARTED -->
## Iniciando

TODO

### Pre-requisitos

Instale o Python 3.8.2

### Instalação

1. Download, crie &. ative um virtualenv
  - `git clone https://github.com/turicas/covid19-br.git`
  - `virtualenv venv`
  - `source venv/bin/activate`
2. Instale as dependências:
  - Script de consolidação e robô: `pip install -r requirements.txt`
  - Extratores de dados estaduais: `pip install -r requirements-collect.txt`
3. Rode o script de coleta: 
  - `./collect.sh`
  - O objetivo desse script é # TODO: adicionar o objetivo desse arquivo, ex pq so tem 3 estados
4. Rode o script de consolidação: 
  - `./run.sh`
  - O objetivo desse script é # TODO: adicionar o objetivo desse arquivo...
5. Verifique o resultado em `data/output`.
```
data
│   epidemiological-week.csv
│   populacao-estimada-2019.csv   
│
└───download
    │   ...
|
└───error
    │   ...
|
└───log
    │   ...
|
└───output
    │   boletim.csv.gz
    │   caso-ce.csv  
    │   caso-pr.csv  
    │   caso-sp.csv  
    │   caso.csv.gz
````

<!-- USAGE EXAMPLES -->
## Utilização

TODO


<!-- ROADMAP -->
## Roadmap

TODO, o que precisa ser feito, prioridades etc


<!-- CONTRIBUTING -->
## Contribuindo

Você pode contribuir de diversas formas:

- Criando programas (crawlers/scrapers/spiders) para extrair os dados automaticamente ([LEIA ISSO ANTES](#criando-scrapers));
- Coletando links para os boletins de seu estado;
- Coletando dados sobre os casos por município por dia;
- Entrando em contato com a secretaria estadual de seu estado, sugerindo as
  [recomendações de liberação dos dados](recomendacoes.md);
- Evitando contato com humanos, lavando as mãos várias vezes ao dia, sendo solidário aos mais vulneráveis;

Para se voluntariar, [siga estes passos](CONTRIBUTING.md).

Procure o seu estado [nas issues desse
repositório](https://github.com/turicas/covid19-br/issues) e vamos conversar
por lá.

## Dados TODO: melhorar descricao & talvez subdividr

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

### Analisando os dados

Caso queira analisar os dados usando SQL, veja o script
[`analysis.sh`](analysis.sh) (ele baixa e converte os CSVs para um banco de
dados SQLite e já cria índices e *views* que facilitam o trabalho) e os
arquivos na pasta [`sql/`](sql/). Por padrão o script reutiliza os arquivos
caso já tenha baixado; para sempre baixar a versão mais atual dos dados,
execute `./analysis.sh --clean`.

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

## VEJA TAMBÉM

- [Outros datasets relevantes](datasets-relevantes.md)
- [Recomendações para secretarias de saúde na disponibilização de
  dados](recomendacoes.md)


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


<!-- LICENSE -->
## Licença e Citação

A licença do código é [LGPL3](https://www.gnu.org/licenses/lgpl-3.0.en.html) e
dos dados convertidos [Creative Commons Attribution
ShareAlike](https://creativecommons.org/licenses/by-sa/4.0/). Caso utilize os
dados, **cite a fonte original e quem tratou os dados** e caso compartilhe os
dados, **utilize a mesma licença**.
Exemplos de como os dados podem ser citados:
- **Fonte: Secretarias de Saúde das Unidades Federativas, dados tratados por Álvaro Justen e equipe de voluntários [Brasil.IO](https://brasil.io/)**
- **Brasil.IO: boletins epidemiológicos da COVID-19 por município por dia, disponível em: https://brasil.io/dataset/covid19/ (última atualização: XX de XX de XXXX, acesso em XX de XX de XXXX).**



<!-- CONTACT -->
## Contato

TODO


## Clipping

Quer saber quais projetos e notícias estão usando nossos dados? [Veja o
clipping](clipping.md).


<!-- ACKNOWLEDGEMENTS -->
## Agradecimentos

TODO
