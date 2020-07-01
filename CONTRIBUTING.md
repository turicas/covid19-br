# Colaborando

É possível colaborar de duas formas, coletando dados divulgados pelas Sec. de Saúde dos Estados, ou participando do projeto no Github, propondo melhorias, revisando código, discutindo nas issues e afins.

Nas próximas seções, será explicado, em linhas gerais, como funciona a comunicação entre colaboradores e o preenchimento das planilhas de dados.

Para maiores detalhes, acesso o [documento com a metodologia](https://docs.google.com/document/d/1escumcbjS8inzAKvuXOQocMcQ8ZCqbyHU5X5hFrPpn4/edit?usp=sharing) mais detalhada.

## Coletando Dados

Para participar do time de coleta de dados, acesse [este link](https://bit.ly/covid19-br-help) faça o cadastro e forneça as informações solicitadas no canal `#covid19-onboarding`.

Serão solicitados alguns dados pessoais, para que possamos manter o controle dos voluntários ativos, e em seguida nossa equipe irá alocar você em um Estado que esteja com maior necessidade de ajuda.

### Canais de comunicação

#### Gerais

Existem dois canais que todos os voluntários devem fazer parte, são eles :

- #covid19
- #covid19-anuncios

O #covid19 serve para discussão de duvidas gerais entre todos os voluntários, e o #covid19-anuncios serve para anuncios dos administradores do projeto sobre atualização de dados e outros informes importantes, e é fechado para conversas.

#### Regionais

Para coordenação dos trabalhos de coleta e checagem, você deve então acessar os canais correspondentes às regiões dos estados onde você foi alocado, são eles :

- #covid19-centro-oeste
- #covid19-nordeste
- #covid19-norte
- #covid19-sudeste
- #covid19-sul

Poderá haver ao menos um coordenador por região, que deve ficar atento às atualizações dos estados, para manter as planilhas sempre atualizadas assim que os boletins forem divulgados, e cobrar as checagens dos dados.

### Sistema

Para acesso ao sistema de envio de planilhas com os dados coletados, é necessário fazer o [cadastro no site do Brasil.IO](https://brasil.io/auth/entrar/).

É necessário que você use o mesmo nome de usuário utilizado no cadastro feito em https://chat.brasil.io.

Com o acesso ao sistema, você terá acesso ao Estado que foi designado, e assim poderá anexar a planilha com os dados coletados.

O sistema fornece um modelo de planilha, para cada Estado, com todos os municípios, e as colunas `confirmado` e `mortes` em branco.

Sempre que houver atualização de dados para o Estado, você deve :

* informar a data de referência dos dados;
* anexar a planilha preenchida;
* informar o(s) link(s) onde as informações foram obtidas;
* informar observações relevantes.

[Veja aqui](https://drive.google.com/open?id=1pORD1BtOJsuQR-MqXcIAPwddx4WBe_mu) um vídeo explicando como deve ser usado o sistema.

#### Planilha Modelo

Segue um trecho da planilha de exemplo para o Estado de Alagoas :

```csv
municipio,confirmados,mortes
TOTAL NO ESTADO,,
Importados/Indefinidos,,
Água Branca,,
Anadia,,
Arapiraca,,
Atalaia,,
Barra de Santo Antônio,,
Barra de São Miguel,,
Batalha,,
Belém,,
...
```

A linha `TOTAL NO ESTADO` deve ser preenchida sempre com o total informado pela SES (e não pela soma dos municípios).

Casos e óbitos em que o município não estiver claro ou for de outros estados/ países devem ser inseridos na linha `Importados/Indefinidos`.

Se a SES não divulgou os dados dos municípios, somente a linha `TOTAL NO ESTADO` deve ser preenchida (não preencher `Importados/Indefinidos`).
