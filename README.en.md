[🇧🇷 Português](README.md)

# covid19-br

![pytest@docker](https://github.com/turicas/covid19-br/workflows/pytest@docker/badge.svg)

This repository unifies links and data about reports on the number of cases from State Health Secretariats (Secretarias Estaduais de Saúde - SES), about the cases of covid19 in Brazil (at each city, daily), amongst other data relevant for analysis, such as deaths tolls accounted for in the notary service (by state, daily).

## License and Quotations

The code's license is [LGPL3](https://www.gnu.org/licenses/lgpl-3.0.en.html) and the converted data is [Creative Commons Attribution ShareAlike](https://creativecommons.org/licenses/by-sa/4.0/). In case you use the data, **mention the original data source and who treated the data** and in case you share the data, **use the same license**.
Example of how the data can be quoted:
- **Source: Secretarias de Saúde das Unidades Federativas, data treated by Álvaro Justen and a team of volunteers [Brasil.IO](https://brasil.io/)**
- **Brasil.IO: epidemiological reports of COVID-19 by city daily, available at: https://brasil.io/dataset/covid19/ (last checked in: XX of XX of XXXX, access in XX XX, XXXX).**


## Data

The data, after collected and treated, stays available in 3 ways on [Brasil.IO](https://brasil.io/):

- [Web Interface](https://brasil.io/dataset/covid19) (made for humans)
- [API](https://brasil.io/api/dataset/covid19) (made for humans that develop apps) - [see available API documentation](api.md)
- [Full dataset download](https://data.brasil.io/dataset/covid19/_meta/list.html)

In case you want to access the data before they are published (ATTENTION: they may not have been checked yet), you can [access directly the sheets in which we are working on](https://drive.google.com/open?id=1l3tiwrGEcJEV3gxX0yP-VMRNaE1MLfS2).

If this program and/or the resulting data are useful to you or your company, **consider [donating to the project Brasil.IO](https://brasil.io/doe)**, which is maintained voluntarily.


### FAQ ABOUT THE DATA

**Before contacting us to ask questions about the data (we're quite busy), [CHECK OUR FAQ](faq.md)** (still in Portuguese).

For more information [see the data collection methodology](https://drive.google.com/open?id=1escumcbjS8inzAKvuXOQocMcQ8ZCqbyHU5X5hFrPpn4).

### Analyzing the data

In case you want to analyze our data using SQL, look at the script [`analysis.sh`](analysis.sh) (it downloads and transforms CSVs to an SQLite database and create indexes and views that make the job easier) and the archives in the folder [`sql/`](sql/).

By default, the script reuses the same files if they have already been
downloaded; in order to always download the most up-to-date version of
the data, run `./analysis.sh --clean`.

### Validating the data

The metadata are described like the *Data Package* and
*[Table Schema](https://specs.frictionlessdata.io/table-schema/#language)* standards of
*[Frictionless Data](https://frictionlessdata.io/)*. This means that the data can be automatically validated to detect, for example, if the values of a field conform with the type defined, if a date is valid, if columns are missing or if there are duplicated lines.

To verify, activate the virtual Python environment and after that type:

```
goodtables data/datapackage.json
```

The report from the tool *[Good Tables](https://github.com/frictionlessdata/goodtables-py)* will indicate if there are any inconsistencies. The validation can also be done online through [Goodtables.io](http://goodtables.io/).

## Contributing

You can contribute in many ways:

- Building programs (crawlers/scrapers/spiders) to extract data automatically ([READ THIS BEFORE](#criando-scrapers));
- Collecting links for your state reports;
- Collecting data about cases by city daily;
- Contacting the State Secretariat from your State, suggesting the [recommendations for data release](recomendacoes.md);
- Avoiding physical contact with humans;
- Washing your hands several times a day;
- Being solidary to the most vulnerable;

In order to volunteer, [follow these steps](CONTRIBUTING.md).

Look for your state [in this repository's issues](https://github.com/turicas/covid19-br/issues) and let's talk through there.

### Creating Scrapers

We're changing the way we upload the data to make the job easier for volunteers and to make the process more solid and reliable and, with that, it will be easier to make so that bots can also upload data; that being said, scrapers will help *a lot* in this process. However, when creating a scraper it is important that you follow a few rules:

- It's **required** that you create it using `scrapy`;
- **Do Not** use `pandas`, `BeautifulSoap`, `requests` or other unnecessary libraries (the standard Python lib already has lots of useful libs, `scrapy` with XPath is already capable of handling most of the scraping and `rows` is already a dependency of this repository);
- There must be an easy way to make the scraper collect reports and cases for an specific date (but it should be able to identify which dates the data is available for and to capture several dates too);
- The parsing method must return (with `yield`) a dictionary with the following keys:
  - `date`: in the format `"YYYY-MM-DD"`
  - `state`: the state initials, with 2 characters in caps (must be an attribute from the class of the spider and use `self.state`)
  - `city` (city name or blank, in case its the state's value, it must be `None`)
  - `place_type`: use `"city"` when it's municipal data and `"state"` it's from the whole state
  - `confirmed`: integer, number of cases confirmed (or `None`)
  - `deaths`: integer, number of deaths on that day (or `None`)
  - **ATTENTION**:	the scraper must always return a register to the state that *isn't* the sum of values by city (this data should be extracted by a row named "total in state" in the report) - this row will have the column `city` with the value `None` and `place_type` with `state` - this data must come filled as being the sum of all municipal values *in case the report doesn't have the totalling data*
- When possible, use automated tests;

Right now we don't have much time available for reviews, so **please**, only create a pull request with code of a new scraper if you can fulfill the requirements above.

## Installing

### Default

Requires Python 3 (tested in 3.8.2). To set up your environment:

- Install Python 3.8.2
- Create a virtualenv
- Install the dependencies:
  - Consolidation script and bot: `pip install -r requirements.txt`
  - States data extractors: `pip install -r requirements-collect.txt`
- Run the collect script: `./collect.sh`
- Run the consolidation script: `./run.sh`

Check the output in `data/output`.

### Docker

If you'd rather use Docker to execute, you just need to follow these steps: 
 
```shell
make docker-build   # to build the image
make docker-collect # to collect the data
make docker-run     # to consolidate the data
```

## SEE ALSO

- [Other relevant datasets](datasets-relevantes.md)
- [Recommendations for the State Secretariats' data release](recomendacoes.md)


## Clipping

Wanna see which projects and news are using our data? [See the clipping](clipping.md).


## Data Update on Brasil.IO

Create a `.env` file with the correct values to the following environment variables: 

```shell
BRASILIO_SSH_USER
BRASILIO_SSH_SERVER
BRASILIO_DATA_PATH
BRASILIO_UPDATE_COMMAND
```

Run the script:

`./deploy.sh`

It will collect the data from the sheets (that are linked in
`data/boletim_url.csv` and `data/caso_url.csv`), add the data to the repository, compact them, send them to the server, and execute the dataset update command.

> Note: the script that automatically downloads and converts data must
> be executed separately, with the command `./collect.sh`.
