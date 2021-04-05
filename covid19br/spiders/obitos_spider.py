import datetime
import json
from urllib.parse import urlencode, urljoin

import scrapy
from scrapy.http.cookies import CookieJar

STATES = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()
ETHNICITY_CHOICES = "I AMARELA BRANCA IGNORADA INDIGENA PARDA PRETA".split()
PLACE_CHOICES = "HOSPITAL DOMICILIO VIA_PUBLICA OUTROS".split()
CHART_TYPE_CHOICES = {
    "respiratory": {"name": "chart5", "url": "https://transparencia.registrocivil.org.br/api/covid-covid-registral",},
    "cardiac": {"name": "chartCardiac4", "url": "https://transparencia.registrocivil.org.br/api/covid-cardiaco",},
}


def qs_to_dict(data):
    """
    >>> result = qs_to_dict([("a", 1), ("b", 2)])
    >>> expected = {'a': 1, 'b': 2}
    >>> result == expected
    True
    >>> result = qs_to_dict([("b", 0), ("a", 1), ("b", 2)])
    >>> expected = {'a': 1, 'b': [0, 2]}
    >>> result == expected
    True
    """
    from collections import defaultdict

    new = defaultdict(list)
    for key, value in data:
        new[key].append(value)
    return {key: value if len(value) > 1 else value[0] for key, value in new.items()}


class BaseRegistroCivilSpider(scrapy.Spider):
    cookie_jar = CookieJar()
    login_url = "https://transparencia.registrocivil.org.br/especial-covid"
    start_urls = []
    xsrf_token = ""
    custom_settings = {
        "USER_AGENT": "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.44 Safari/537.36",
    }

    def start_requests(self):
        yield self.make_login_request()

    def make_login_request(self):
        return scrapy.Request(url=self.login_url, callback=self.parse_login_response, meta={"dont_cache": True},)

    def make_request(self, *args, **kwargs):
        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["X-XSRF-TOKEN"] = self.xsrf_token
        return scrapy.Request(*args, **kwargs)

    def start_requests_after_login(self):
        for url in self.start_urls:
            yield self.make_request(url, callback=self.parse)

    def parse_login_response(self, response):
        self.cookie_jar.extract_cookies(response, response.request)
        self.xsrf_token = next(c for c in self.cookie_jar if c.name == "XSRF-TOKEN").value

        for request in self.start_requests_after_login():
            yield request

    def parse(self):
        raise NotImplementedError()


class DeathsSpider(BaseRegistroCivilSpider):
    name = "obitos"
    causes_map = {
        "respiratory": {
            "COVID": "covid19",
            "INDETERMINADA": "indeterminate",
            "INSUFICIENCIA_RESPIRATORIA": "respiratory_failure",
            "OUTRAS": "others",
            "PNEUMONIA": "pneumonia",
            "SEPTICEMIA": "septicemia",
            "SRAG": "sars",
        },
        "cardiac": {
            "AVC": "avc",
            "CARDIOPATIA": "cardiopathy",
            "CHOQUE_CARD": "cardiac_shock",
            "COVID_AVC": "covid19",
            "COVID_INFARTO": "covid19",
            "INFARTO": "heart_attack",
            "SUBITA": "sudden",
        },
    }

    def start_requests_after_login(self):
        for state in STATES:
            for year in [2021, 2020, 2019]:
                yield self.make_chart_request(
                    "respiratory",
                    start_date=datetime.date(year, 1, 1),
                    end_date=datetime.date(year, 12, 31),
                    state=state,
                    dont_cache=True,
                )

    def make_chart_request(
        self, chart_type, start_date, end_date, state, ethnicity="I", places="all", dont_cache=False
    ):
        if ethnicity not in ETHNICITY_CHOICES:
            raise ValueError(f"Unknown ethnicity {repr(ethnicity)}")

        if places == "all":
            places = PLACE_CHOICES
        elif not isinstance(places, (list, tuple)):
            raise TypeError(f"Invalid place type {type(places)}")
        else:
            for place in places:
                if place not in PLACE_CHOICES:
                    raise ValueError(f"Unknown place {repr(place)}")

        if chart_type not in CHART_TYPE_CHOICES:
            raise ValueError("Unknown chart type {repr(chart_type)}")

        base_url = CHART_TYPE_CHOICES[chart_type]["url"]
        data = [
            ("start_date", str(start_date)),
            ("end_date", str(end_date)),
            ("city_id", "all"),
            ("state", state),
            ("diffCity", "false"),
            ("cor_pele", ethnicity),
        ]
        for place in places:
            data.append(("places[]", place))
        data.append(("chart", CHART_TYPE_CHOICES[chart_type]["name"]))

        return self.make_request(
            url=urljoin(base_url, "?" + urlencode(data)),
            headers={"X-XSRF-TOKEN": self.xsrf_token},
            callback=self.parse_chart_response,
            meta={"row": qs_to_dict(data), "dont_cache": dont_cache, "chart_type": chart_type},
        )

    def parse_chart_response(self, response):
        meta = response.meta
        state = meta["row"]["state"]
        chart_type = meta["chart_type"]
        data = json.loads(response.body)
        causes_map = self.causes_map[chart_type]

        for date, chart in data["chart"].items():
            row = {"date": date, "state": state}
            for cause, cause_data in chart.items():
                row["cause"] = causes_map[cause]
                row["total"] = cause_data[0]["total"]
                yield row
