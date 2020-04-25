# FAQ sobre os Dados

Para entender quais decisões tomamos no trabalho de coleta, normalização e
checagem dos dados [veja a metodologia de coleta de
dados](https://drive.google.com/open?id=1escumcbjS8inzAKvuXOQocMcQ8ZCqbyHU5X5hFrPpn4).

## Como citar a base de dados COVID-19 do Brasil.IO?

Leia a seção [Licença e citação](https://github.com/turicas/covid19-br/blob/master/README.md#licen%C3%A7a-e-cita%C3%A7%C3%A3o) do README desse repositório.


## As contagens estaduais podem ser diferentes das municipais?

**Sim**, por 2 motivos:

1. Secretaria Estadual de Saúde (SES) parou de divulgar dados por município e
   está somente divulgando por estado (isso aconteceu com SP durante alguns
   dias);
2. A SES divulgou um dado incorreto (às vezes acontece).


## Os dados do Ministério da Saúde estão diferentes dos dados do Brasil.IO. Qual está correto?

Nem sempre nossos dados baterão com os do Ministério da Saúde, pois pode ser
que nossa coleta seja feita depois da coleta do Ministério e, com isso, teremos
dados mais atuais. Também pode acontecer o caso de a Secretaria Estadual
informar ao Ministério da Saúde os dados antes de emitir um boletim público -
nesse caso nossos dados estarão desatualizados com relação ao Ministério.


## Somei os casos por município de um estado e ele diverge do total no estado. O dado de vocês está errado! Como posso consertar?

**Provavelmente não está errado**. Nem sempre as Secretarias divulgam todos os
municípios em que aconteceram casos. Para um dado entrar na plataforma ele é
checado por nossos voluntários - isso não elimina a possibilidade de erro, mas
a probabilidade é baixa.


## Alguns municípios não possuem dados ou não possuem dados para muitas datas, como devo proceder para pegar o histórico?

Só temos dados disponíveis a partir do primeiro caso confirmado/divulgado pela
Secretaria Estadual de Saúde.


## O site da prefeitura do meu município tem dados mais atuais que os de vocês! Como devo fazer para atualizar?

Nós só estamos coletando dados das Secretarias Estaduais de Saúde. Toda a
coleta é feita manualmente e temos muito trabalho para coletar e checar esses
dados, dado que eles não estão disponíveis em formatos abertos e estruturados.
Se você quer colaborar, cobre da SES do seu estado a divulgação dos dados em
formatos abertos e estruturados.


## Onde estão os números de casos suspeitos e excluídos?

Por uma questão metodológica, não estamos coletando esses dados e não vamos
incluí-los. Por favor, não insista.


## A API não está limitando a quantidade de casos, o que pode ser?

A API tem paginação (10.000 registros por página). Você deve requisitar a
página que está linkada em `next` no resultado.


## Por que o número de óbitos dos cartórios divulgado pelo Brasil.IO está diferente do divulgado pelo Portal da Transparência do Registro Civil?

Até onde verificamos, os dados do Portal da Transparência do Registro Civil
atualiza os dados a cada hora e mesmo dados de óbitos para dias anteriores
podem mudar (estamos coletando a data do óbito, não do registro do óbito). Como
fazemos sempre uma coleta inteira dos dados, optamos por não atualizar essa
tabela de hora em hora, para não sobrecarregar os servidores do Portal. Por
isso, é esperado que exista alguma diferença nos dados de óbitos,
principalmente para as datas mais recentes.

Além disso, como os números de óbitos por covid19 são de casos suspeitos e
confirmados, alguns casos suspeitos podem ser negativados e o número total
*diminuir*.
