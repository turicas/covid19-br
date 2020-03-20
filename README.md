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

Acesse os dados no [dataset covid19 no
Brasil.IO](https://brasil.io/dataset/covid19).

Acesse diretamente as planilhas, com separação por UF:

- [Boletins](https://drive.google.com/open?id=11dZ0Ikcpnq2mBCP_B4ltOfM1OIvuuP_WLwGtHih4lXI)
- [Casos](https://drive.google.com/open?id=1kjeKS6YOdL9lOxhob1E_m2zg9sysYseriFLOfDSgHAg)

Se esse programa e/ou os dados resultantes foram úteis a você ou à sua empresa,
considere [fazer uma doação ao projeto Brasil.IO](https://brasil.io/doe), que é
mantido voluntariamente.


## Contribuindo

Você pode contribuir de diversas formas:

- Coletando links para os boletins de seu estado;
- Coletando dados sobre os casos por município por dia;
- Entrando em contato com a secretaria estadual de seu estado, sugerindo as
  [recomendações de liberação dos dados](recomendacoes.md);
- Evitando contato com humanos;
- Lavando as mãos várias vezes ao dia;
- Sendo solidário aos mais vulneráveis;

Procure o seu estado [nas issues desse
repositório](https://github.com/turicas/covid19-br/issues) e vamos conversar
por lá.


## Instalando

Necessita de Python 3 (testado em 3.8.2). Para montar seu ambiente:

- Instale o Python 3.8.2
- Crie um virtualenv
- Instale as dependências: `pip install -r requirements.txt`
- Rode o script de coleta: `./collect.sh`
- Rode o script de consolidação: `./run.sh`

Verifique o resultado em `data/output`.


## VEJA TAMBÉM

- [Outros datasets relevantes](datasets-relevantes.md)
- [Recomendações para secretarias de saúde na disponibilização de
  dados](recomendacoes.md)
