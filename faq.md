# FAQ sobre os Dados

Para entender quais decisões tomamos no trabalho de coleta, normalização e
checagem dos dados [veja a metodologia de coleta de
dados](https://drive.google.com/open?id=1escumcbjS8inzAKvuXOQocMcQ8ZCqbyHU5X5hFrPpn4).


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
