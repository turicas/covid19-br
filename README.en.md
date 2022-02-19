[🇧🇷 Português](README.md)

# covid19-br

![pytest@docker](https://github.com/turicas/covid19-br/workflows/pytest@docker/badge.svg) ![goodtables](https://github.com/turicas/covid19-br/workflows/goodtables/badge.svg)

This repository unifies links and data about reports on the number of cases
from State Health Secretariats (Secretarias Estaduais de Saúde - SES), about
the cases of covid19 in Brazil (at each city, daily), amongst other data relevant
for analysis, such as deaths tolls accounted for in the notary service (by state, daily).

## Table of Contents
1. [License and Quotations](#license-and-quotations)
2. [About the data](#data)
3. [General Contribution Guide](#contributing)
4. [Project installation / setup guide (development environment)](#installing)
5. [Guide on how to run existing scrapers](#running-the-scrapers)
6. [Guide on creating new scrapers](#creating-new-scrapers)
7. [Guide on how to update data in Brasil.io (production environment)](#data-update-on-brasilio)

## License and Quotations

The code's license is [LGPL3](https://www.gnu.org/licenses/lgpl-3.0.en.html) and the
converted data is [Creative Commons Attribution ShareAlike](https://creativecommons.org/licenses/by-sa/4.0/).
In case you use the data, **mention the original data source and who treated the data**
and in case you share the data, **use the same license**.
Example of how the data can be quoted:
- **Source: Secretarias de Saúde das Unidades Federativas, data treated by Álvaro Justen and a team of volunteers [Brasil.IO](https://brasil.io/)**
- **Brasil.IO: epidemiological reports of COVID-19 by city daily, available at: https://brasil.io/dataset/covid19/ (last checked in: XX of XX of XXXX, access in XX XX, XXXX).**


## Data

The data, after collected and treated, stays available in 3 ways on [Brasil.IO](https://brasil.io/):

- [Web Interface](https://brasil.io/dataset/covid19) (made for humans)
- [API](https://brasil.io/api/dataset/covid19) (made for humans that develop apps) - [see available API documentation](api.md)
- [Full dataset download](https://data.brasil.io/dataset/covid19/_meta/list.html)

In case you want to access the data before they are published (ATTENTION: they 
may not have been checked yet), you can [access directly the sheets in which we
are working on](https://drive.google.com/open?id=1l3tiwrGEcJEV3gxX0yP-VMRNaE1MLfS2).

If this program and/or the resulting data are useful to you or your company,
**consider [donating to the project Brasil.IO](https://brasil.io/doe)**, which
is maintained voluntarily.


### FAQ ABOUT THE DATA

**Before contacting us to ask questions about the data (we're quite busy),
[CHECK OUR FAQ](faq.md)** (still in Portuguese).

For more information [see the data collection 
methodology](https://drive.google.com/open?id=1escumcbjS8inzAKvuXOQocMcQ8ZCqbyHU5X5hFrPpn4).

### Clipping

Wanna see which projects and news are using our data? [See the clipping](clipping.md).

### Analyzing the data

In case you want to analyze our data using SQL, look at the script
[`analysis.sh`](analysis.sh) (it downloads and transforms CSVs to 
an SQLite database and create indexes and views that make the job easier)
and the archives in the folder [`sql/`](sql/).

By default, the script reuses the same files if they have already been
downloaded; in order to always download the most up-to-date version of
the data, run `./analysis.sh --clean`.

Also read our [review of the vaccination microdata available on 
OpenDataSUS](analises/microdados-vacinacao/README.md) (still in Portuguese).

### Validating the data

The metadata are described like the *Data Package* and
*[Table Schema](https://specs.frictionlessdata.io/table-schema/#language)* standards
of *[Frictionless Data](https://frictionlessdata.io/)*. This means that the data can
be automatically validated to detect, for example, if the values of a field conform
with the type defined, if a date is valid, if columns are missing or if there are
duplicated lines.

To verify, activate the virtual Python environment and after that type:

```
goodtables data/datapackage.json
```

The report from the tool 
*[Good Tables](https://github.com/frictionlessdata/goodtables-py)* will 
indicate if there are any inconsistencies. The validation can also be done
online through [Goodtables.io](http://goodtables.io/).

### Further readings

- [Other relevant datasets](datasets-relevantes.md)
- [Recommendations for the State Secretariats' data release](recomendacoes.md)


## Contributing

You can contribute in many ways:

- Building programs (crawlers/scrapers/spiders) to extract data automatically
  ([READ THIS BEFORE](#creating-new-scrapers));
- Collecting links for your state reports;
- Collecting data about cases by city daily;
- Contacting the State Secretariat from your State, suggesting the
  [recommendations for data release](recomendacoes.md);
- Avoiding physical contact with humans;
- Washing your hands several times a day;
- Being solidary to the most vulnerable;

In order to volunteer, [follow these steps](CONTRIBUTING.md).

Look for your state [in this repository's
issues](https://github.com/turicas/covid19-br/issues)
and let's talk through there.

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

This project requires Python 3 (tested in 3.8.2) and Scrapy.

You can build your development environment using the
[default setup](#default-setup) or [setup with docker](#docker-setup).

### Default setup

Requires Python 3 (tested in 3.8.2). To set up your environment:

1. Install Python 3.8.2
2. Create a virtualenv (you can use
   [venv](https://docs.python.org/pt-br/3/library/venv.html) for this).
3. Install the dependencies: `pip install -r requirements-development.txt`

### Docker setup

If you'd rather use Docker to execute, you just need to follow these steps:

```shell
make docker-build       # to build the image
make docker-run-spiders # to collect data
```

## Running the scrapers

Once your [setup](#installing) is finished, you can run **all scrapers**
using one of the following commands in your terminal (depending on the type of
setup you decided to do):


```shell
python covid19br/run_spider.py  # if you are using the default setup
make docker-run-spiders         # if you are usinf the docker setup
```

The above commands will run the scrappers for **all available states**
that we have implemented, fetching the data for **today's date** and 
**will save the consolidated** in a `.csv` in the folder `data` from
this directory (by default they are saved in files with this name pattern
`"data/{estado}/covid19-{estado}-{data}{extra_info}.csv"`).

But this is not the only way to use this command, you can choose not to save the
consolidated in a `.csv` (only display them on the screen) or run only scrapers
for some specific states or for other specific days that are not necessarily
today's date.

To better adapt the command to your use case you can run it in the terminal with
the following options:

> NOTE: If you are using docker, just add `docker container run --rm
  --name covid19-br -v $(PWD)/data:/app/data covid19-br` before any of the
   commands to follow.
   
```shell
# Example of how to scrape data from all states in a date range
python covid19br/run_spider.py --start-date 24/02/2021 --end-date 30/03/2021

# In case you want to run it for specific dates (put them in a list separating them by commas):
python covid19br/run_spider.py --dates-list  15/01/2022,17/01/2022

# To only execute spiders of specific states (list them and separate them by commas):
python covid19br/run_spider.py --states BA,PR

# To check which states are available for scraping:
python covid19br/run_spider.py --available-spiders

# If you don't want to save the csv's, just show the results on the screen:
python covid19br/run_spider.py --print-results-only

# You can consult these and other available options using:
python covid19br/run_spider.py -h
```

# Creating new scrapers

We're changing the way we upload data to make it easier for
volunteers and make the process more robust and reliable and, with that, it will be
easier for robots to upload the data as well; in this way, scrapers
will help *a lot* in the process.

However, when creating a scraper it is important that you follow some rules:

- It is **necessary** to make the scraper using `scrapy` (check out
  [here the docs](https://scrapy.org/));
- **Do not use** `pandas`, `BeautifulSoap`, `requests` or other libraries
   (Python's std lib already has a lot of useful library, `scrapy`
   with XPath already handles most of the scraping and `rows` is already
   a dependency from this repository);

To standardize the way scrapers receive parameters and return data,
we created a [Base Spider](covid19br/common/base_spider.py), which is nothing more than
a basic scrapy spider with extra logic for:
- Identify _for which dates_ the spider should look for data (this information
   is received as a parameter and is stored in the class in the `self.requested_dates` attribute,
   which is a `generator` of values of type `datetime.date` with the dates we need
   scrape the data, and should be used by your spider to fetch the data like
   requested).
- Save the scraped data in a way that it is returned to the
   system that called the scraper in a standardized way.

To standardize the data that is returned by the spiders, we create the class
[FullReport](covid19br/common/models/full_report.py) which represents a "complete
report" and stores all data collected for a given state in a specific date. 
This full report consists of several [bulletins](covid19br/common/models/bulletin_models.py),
(one for each city in the state + one for imported/undefined cases) with the total
number of confirmed cases and number of deaths for that day.

Your script doesn't need to worry about creating the `FullReport` object that will be
returned, this is the responsibility of the [Base Spider](covid19br/common/base_spider.py),
what your spider should create are the [bulletins](covid19br/common/models/bulletin_models.py)
with the data it collects and save these `bulletins` in the report via the
`add_new_bulletin_to_report` provided by `Spider Base`.

In summary, when creating a new state spider keep in mind:
- It is desirable that you create your spider by extending the 
  [Spider Base](covid19br/common/base_spider.py) class (you can
  check some examples of how other spiders are implemented in the
  [/covid19br/spiders](covid19br/spiders) folder).
- A full spider is able to collect:
    - Number of confirmed cases and number of deaths **per city** in the state;
    - Number of confirmed cases and number of deaths **imported/undefined**;
    - Confirmed case numbers and **total** death numbers for the state (this
      value is computed automatically as the above cases are obtained,
      but in cases where the secretariat provides it, we choose it as the
      "source of truth".
    - For different dates (from the beginning of the pandemic until today).
    > OBS: As there is no standardization in the way in which the secretariats provide the
    data, it is not always possible to obtain all this information as we wish. Eve if you
    can get only a part of the information in an automated way, it can already be a good 
    start and a valid contribution! :)
- The collected data must be saved in [bulletins](covid19br/common/models/bulletin_models.py)
  and added to the spider's return via the `add_new_bulletin_to_report` method.

When you finish implementing your spider, add it to the list of spiders in the script
[run_spider.py](covid19br/run_spider.py) and run it (more info on how to do
this in the previous section). If everything went as expected, a `.csv` is expected to be created.
in the `/data/...` folder with the data scraped by your spider :)

At the moment we don't have much time available for review, so **please**,
only create a *pull request* with code from a new scraper if you can fulfill the
above requirements.

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
`data/boletim_url.csv` and `data/caso_url.csv`), add the data to
the repository, compact them, send them to the server, and execute
the dataset update command.

> Note: the script that automatically downloads and converts data must
> be executed separately, with the command `./run-spiders.sh`.
