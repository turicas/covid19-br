# Recomendações para Liberação de Dados


## Para Secretarias de Saúde

Oi! Obrigado por chegar até aqui. Nesse momento é muito importante que os
cidadãos saibam **o quanto antes** a situação da covid-19 **em seus
municípios**. Para que jornalistas e outras pessoas tenham acesso a esse dado
da maneira mais rápida possível, sugerimos que:

### Libere os dados por município

Ter os dados consolidados por estado ajuda, mas a população vive em municípios
e as ações relacionadas à contenção do vírus devem mudar mais rapidamente nos
municípios com mais casos. Por isso, disponibilizem os dados por município, se
possível com granularidade total (casos notificados, suspeitos, confirmados,
mortes etc.).


### Consolide e Padronize os Informativos

- Crie uma página específica para listar todos os boletins do COVID19. Exemplo:
  [PR](http://www.saude.pr.gov.br/modules/conteudo/conteudo.php?conteudo=3507).
- Padronize o link para download dos arquivos, exemplo:
  https://www.saude.UF.gov.br/covid19/boletim-2020-03-20.csv


### Libere os Dados em Formato Estruturado e Aberto

Muitas secretarias disponibilizam os dados em imagens, PDFs ou mesmo em texto
corrido dentro de uma notícia do site. Isso dificulta muito qualquer tipo de
extração e análise dos dados. Outras, disponibilizam painéis onde não é possível
fazer download dos dados completos. Recomendações:

- Disponibilize os dados em formato de planilha;
- Evite colocar imagens e outras informações na planilha: coloque apenas o
  cabeçalho com os nomes das colunas e os valores. Informações como fonte dos
  dados, logotipo da Secretaria, dentre outras podem ficar no site da
  Secretaria;
- Para uma mesma coluna, não altere o tipo de dado (exemplo: na coluna de
  número de casos confirmados, coloque apenas números, não adicione asteriscos,
  parenteses ou outros caracteres);
- Para facilitar a leitura dos dados, a planilha disponível deve estar em um
  dos seguintes formatos (nessa ordem de prioridade):
  - CSV
  - ODS
  - XLSX
  - XLS

### Download dos dados

É muito importante que o endereço para download dos dados seja padronizado,
dessa forma o processo de coleta pode ser facilmente automatizável.

Exemplo, para o dia 01/05/2020, o link para download do CSV poderia ser:
https://www.saude.uf.gov.br/covid19/boletim/2020-05-01.csv

Também é importante existir uma página que possua links para todos os boletins
disponíveis.


#### Para dados agregados

Nessa planilha, cada município que possui casos confirmados deve ter uma linha
por dia, com os valores agregados para aquela data. As colunas são:

- `data`: data a qual a informação se refere (seguir padrão ISO 8601 (AAAA-MM-DD)
  Ex.: 2020-05-17 equivale a 17 de Maio de 2020)
- `uf`: sigla da unidade da federação na qual o caso pertence (quando é um caso
  importado de outro estado, pode ser usado um outro estado ou deixar a célula
  vazia, caso não se saiba).
- `municipio`: nome do município [segundo essa
  planilha](https://raw.githubusercontent.com/turicas/covid19-br/master/data/populacao-estimada-2019.csv);
  pode ser também "Importado", "Indefinido" ou "TOTAL NO ESTADO" (esse último
  para nessa linha divulgar o número total oficial para aquela data).
- `codigo_ibge`: código IBGE do município com 7 dígitos (retirar da planilha
  acima, que é dos dados do IBGE) - no caso de município "Importado",
  "Indefinido" ou "TOTAL NO ESTADO", deixar vazio.
- `casos_confirmados`: número (inteiro) acumulado de casos confirmados até a
  data.
- `obitos_confirmados`: número (inteiro) acumulado de óbitos até a data.
- `observacao`: opcional, pode incluir texto livre sobre alguma questão
  específica com relação aos dados desse município, exemplo: "o caso incluído
  no dia anterior estava incorreto e hoje foi remanejado para município o X".

Caso também estejam disponíveis outras informações agregadas (como total de
leitos ocupados, leitos totais no município, total de testes feitos, total de
testes negativos/positivos etc.), pode-se adicionar outras colunas.

> Nota: caso prefira, a Secretaria também pode incluir com os valores "0" os
> municípios que ainda não possuem casos confirmados.

##### CSV Exemplo

Segue um exemplo para o Estado de Alagoas

```csv
data,uf,municipio,codigo_ibge,casos_confirmados,obtitos_confirmados,observacao
2020-05-06,AL,Anadia,2700201,1,1,
2020-05-06,AL,Arapiraca,2700300,37,3,
2020-05-06,AL,Atalaia,2700409,1,0,
2020-05-06,AL,Barra de Santo Antônio,2700508,1,0,
2020-05-06,AL,Barra de São Miguel,2700607,5,0,
2020-05-06,AL,TOTAL NO ESTADO,2700607,45,4,
```

#### Para microdados

Ainda não temos uma recomendação de microdados, por enquanto sugerimos utilizar [o modelo proposto pela Open
Knowledge Foundation
Brasil](https://transparenciacovid19.ok.org.br/files/Toolkit_1_microdados_basicos.pdf).

Veja [aqui](https://docs.google.com/spreadsheets/d/1mgZe2GjKz_7zH5w4cEVfTh4LfvqDlUs3lxFSD6NJFjw/edit) 
um modelo de planilha proposto pela OKBR.


## Para Jornalistas/Ativistas/Cidadãos

É importante que as Secretarias de Saúde entendam que, dependendo do formato e
da qualidade do dado que disponibilizam, ações de divulgação e contenção do
vírus podem ser impactadas - e não podemos perder tempo nesse momento.

Você pode colaborar com esse projeto verificando a qualidade dos dados de uma
determinada Secretaria de Saúde e entrando em contato com sua assessoria de
imprensa, pedindo melhorias. [Veja os boletins
disponíveis](https://brasil.io/dataset/covid19/boletim), clique nos
links e verifique o quão difícil é copiar os dados para uma planilha, lembrando
que idealmente os dados deveriam estar em um formato já estruturado, como uma
planilha (nada de imagens, nada de PDF, nada de números no meio de um texto
corrido na página).

Um exemplo de comunicação que pode ser feita é o email abaixo, que foi enviado
à [Assessoria de Comunicação da Secretaria de Saúde do Estado do
Ceará](https://www.saude.ce.gov.br/institucional/assessoria-de-imprensa/):

```text
Título: Dados COVID19 por município estruturados

Conteúdo:
Olá, tudo bem?

Participo de um projeto cujo objetivo é fornecer dados sobre o covid-19 de
todos os estados brasileiros por município, diariamente, para que a população
dos municípios saiba exatamente o que está acontecendo e possa tomar atitudes
mais rapidamente (as atualizações são feitas várias vezes ao dia, bem mais
rapidamente que o Ministério da Saúde).

Entrei em vosso site, porém não consegui extrair os dados pois eles estão em um
formato que dificulta o acesso, fazendo com que o processo de coleta, análise e
divulgação seja muito maior. Gostaria de sugerir que liberem os dados em
formato estruturado (como uma planilha em CSV, ODS, XLS ou XLSX).

Mais detalhes sobre o projeto em:
  https://twitter.com/turicas/status/1241068121202536448

Os dados já estão disponíveis em:
  https://brasil.io/dataset/covid19

Coloco-me à disposição para ajudar em quaisquer questões técnicas.
Desde já agradeço,
```

> Nota: o conteúdo do email foi levemente alterado para facilitar que você
> copie/cole e envie para outras secretarias.
