# Outros Datasets Relevantes

## Cadastro Nacional de Entidades de Saúde

O [Cadastro Nacional de Entidades de Saúde
(CNES)](http://cnes.datasus.gov.br/), disponibilizado pelo DATASUS, contém
informações sobre estabelecimentos de saúde, profissionais, equipamentos e
diversas outras que podem ser úteis em análises. Baixe os dados
para fevereiro de 2020 em:

- [Fonte oficial (DATASUS)](ftp://ftp.datasus.gov.br/cnes/BASE_DE_DADOS_CNES_202002.ZIP)
- [Mirror do Brasil.IO](https://data.brasil.io/mirror/ftp.datasus.gov.br/cnes/BASE_DE_DADOS_CNES_202002.ZIP)

Caso queira baixar versões antigas, acesse [o mirror do
Brasil.IO](https://data.brasil.io/mirror/ftp.datasus.gov.br/cnes/_meta/list.html)
(o download tende a ser mais rápido que no DATASUS, além de possuir HTTPS em
vez de FTP).

> Nota: os dados estão disponíveis de julho de 2017 a fevereiro de 2019. Para
> baixar para outros meses/anos, troque `202002` pelo `YYYYMM` desejado.


## Estimativa de População 2019

O IBGE disponibiliza [a estimativa de população por município em
2019](https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html?=&t=resultados).

Os dados também estão convertidos nesse CSV:
[data/populacao-estimada-2019.csv](data/populacao-estimada-2019.csv) ([acesse o
script que faz download e conversão desses
dados](https://github.com/turicas/censo-ibge)).
