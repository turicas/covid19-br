[🇧🇷 Português](README.md)

# covid19-br

![pytest@docker](https://github.com/turicas/covid19-br/workflows/pytest@docker/badge.svg)

This repository unifies links and data about reports on the number of cases from the Health State Secretaries (Secretarias Estaduais de Saúde - SES), about the cases of covid19 in Brazil (at each city, daily), amongst other relevant data for analysis, such as deaths by respiratory diseases accounted in the registry (by state, daily).

## License and Quote

The code's license is [LGPL3](https://www.gnu.org/licenses/lgpl-3.0.en.html) and the converted data is [Creative Commons Attribution ShareAlike](https://creativecommons.org/licenses/by-sa/4.0/). In case you use the data, **mention the original font and who treated the data** and in case you share the data, **use the same license**.
Example of how the data can be quoted:
- **Source: Secretarias de Saúde das Unidades Federativas, data treated by Álvaro Justen and team of voluntaries [Brasil.IO](https://brasil.io/)**
- **Brasil.IO: epidemiologic reports of COVID-19 by city daily, available at: https://brasil.io/dataset/covid19/ (last checked in: XX of XX of XXXX, access in XX of XX of XXXX).**


## Data

After collected and treated the data stay available in 3 ways on [Brasil.IO](https://brasil.io/):

- [Web Interface](https://brasil.io/dataset/covid19) (made for humanos)
- [API](https://brasil.io/api/dataset/covid19) (made for humans that develop apps) - [see available API documentation](api.md)
- [Full dataset download](https://data.brasil.io/dataset/covid19/_meta/list.html)

In case you want to access the data before they are published (ATTENTION: they may not have been checked yet), you can [access directly the sheets in which we are working](https://drive.google.com/open?id=1l3tiwrGEcJEV3gxX0yP-VMRNaE1MLfS2).

If this program and/or the data resulting are useful to you or your company, **consider [donating the project Brasil.IO](https://brasil.io/doe)**, which is kept voluntarily.


### FAQ ABOUT DATA

**Before contacting us to consult about the data (we're overloaded), [CONSULT OUR FAQ](faq.md)** (still in Portuguese).

For more information [see the data collection methodology](https://drive.google.com/open?id=1escumcbjS8inzAKvuXOQocMcQ8ZCqbyHU5X5hFrPpn4).

### Analysing data

In case you want to analyze our data using SQL, look at our script [`analysis.sh`](analysis.sh) (it downloads and transforms CSVs to an SQLite database and create indexes and *views* that make the job easier) and the archives in the folder [`sql/`](sql/).

### Validating data

The metadata are described like the standards *Data Package* and
*[Table Schema](https://specs.frictionlessdata.io/table-schema/#language)* of
*[Frictionless Data](https://frictionlessdata.io/)*. This means that the data can be automatically validated to detect, for example, if the values of a field conform with the type defined, if a date is valid, if columns are missing or if there are duplicated lines.

To verify, activate the virtual Python environment and after that type:

```
goodtables data/datapackage.json
```

The report from the tool *[Good Tables](https://github.com/frictionlessdata/goodtables-py)* will indicate if there are any inconsistencies. The validation can also be done *online* through [Goodtables.io](http://goodtables.io/).

## Contributing

You can contribute in many ways:

Building programs (crawlers/scrapers/spiders) to extract data automatically ([READ THIS BEFORE](#criando-scrapers));
Collecting links for your state reports;
Collecting data about your city daily;
Contacting the Secretary of State from your State, suggesting the [recommendations of data release](recomendacoes.md);
Avoiding physical contact with humans;
Washing your hands several times a day;
Being solidary to the most vulnerable;
To volunteer, [folow these steps](CONTRIBUTING.md).

Look for your state [in this repository's issues](https://github.com/turicas/covid19-br/issues) and let's talk through there.

### Creating Scrapers

We're changing the way we upload data to make easier the volunteers job and make the process more solid and reliable and, with that, it will be easier to make that bots can also upload data; that being said, scrapers will help *a lot* in this process, but by creating a Scraper its necessary that you follow a few rules:

- **Necessary** to create  it using `scrapy`;
- **Do Not** use `pandas`, `BeautifulSoap`, `requests` or other unnecessary libraries (the standard Python lib already has lots of useful libs, `scrapy` with XPath is capable of handling most scrapings and `rows` is already a dependency of this repository);
- There must be a way to make the scraper collect reports and cases for an specific date(but it should be able to id to which dates the data is available and to capture several dates too);
- The parsing method must return (with `yield`) a dictionary with the following keys:
  - `date`: in the format `"YYYY-MM-DD"`
  - `state`: the state initials, with 2 characters in caps (must be an attribute from the class of the spider and use `self.state`)
  - `city` (city name or white, in case its the state's value, it must be `None`)
  - `place_type`: use `"city"` when its a municipal data and `"state"` its from the whole state
  - `confirmed`: integer, number of cases confirmed (or `None`)
  - `deaths`: integer, number of deaths that day (ou `None`)
  - **ATTENTION**:	the scraper must always return a register to the state that *isn't* the sum of values by city (this data should be extracted by the column `total in state` at the report) - this line will have the column `city` with the value `None` and `place_type` with `state` - this data must come filled like being the sum of all municipal values *in case the report doesn't have the total data*
- When possible, use automated tests;

Right now we don't have much time available for revision, so **please**, only create a *pull request* with code of a new scraper if you think it can fulfill the requisites above.

## Installing

### Default

Needs Python 3 (tested in 3.8.2). To set up your environment:

- Install Python 3.8.2
- Create a virtualenv
- Install the dependencies:
  - Consolidation script and bot: `pip install -r requirements.txt`
  - States data extractors: `pip install -r requirements-collect.txt`
- Run the collect script: `./collect.sh`
- Run the consolidation script: `./run.sh`

Check the output in `data/output`.

### Docker

If you rather use Docker to execute, you just need to follow these steps: 
 
```shell
make docker-build   # to build the image
make docker-collect # to collect the data
make docker-run     # to consolidate the data
```

## SEE ALSO

- [Other relevant datasets](datasets-relevantes.md)
- [Recommendations for the Secretaries of State's data release](recomendacoes.md)


## Clipping

Wanna see which projects and news are using our data? [See the clipping](clipping.md).


## Data Update in Brasil.IO

Create a `.env` archive with the correct values to the following environment variables: 

```shell
BRASILIO_SSH_USER
BRASILIO_SSH_SERVER
BRASILIO_DATA_PATH
BRASILIO_UPDATE_COMMAND
```

Execute the script:

`./deploy.sh`

It will collect the data from the sheets (that are linked in
`data/boletim_url.csv` and `data/caso_url.csv`), add the data to the repository, compact them, send them to the server, execute the update dataset command.

> Note: the script that downloads and converts data automatically must be executed separately, with the command `./collect.sh`.
