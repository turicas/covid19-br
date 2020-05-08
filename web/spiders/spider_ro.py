import json
import scrapy

from datetime import date
from .base import BaseCovid19Spider


class Covid19ROSpider(BaseCovid19Spider):
    name = "RO"
    start_urls = ["http://covid19.sesau.ro.gov.br"]

    def parse(self, response):
        # extract the displayed date (there's no option to change the date to a past one)
        date_container = response.xpath("//*[text()='calendar_today']/../text()").extract()
        report_date = [t.strip() for t in date_container if t.strip()][0]

        # get the URL for the JS file with the data
        js_script = response.xpath("//attribute::*[contains(., 'estadoRO')]/../@src").extract()[0]
        full_url = response.url + js_script

        year, month, day = [int(v) for v in report_date.split('/')[::-1]]
        self.add_report(date=date(year, month, day), url=full_url)

        yield scrapy.Request(
            url=full_url, meta={"row": {"date": date}}, callback=self.parse_js_data_script
        )

    def parse_js_data_script(self, response):
        """
        The JS code only defines a variable called 'cidades' with the required JSON data to the other
        JS codes work with. This parsing function cleans up the JS file to get only the JSON content.
        """
        json_data = response.body_as_unicode().replace('var cidades = ', '').strip()
        content = json.loads(json_data)

        total_confirmed, total_deaths = 0, 0
        for data in [d['properties'] for d in content['features']]:
            city, confirmed, deaths = data['NOME'], data['confirmados'], data['obitos']
            total_confirmed += confirmed
            total_deaths += deaths

            self.add_city_case(city=city, confirmed=confirmed, deaths=deaths)

        self.add_city_case(city="Importados/Indefinidos", confirmed=None, deaths=None)
        self.add_state_case(confirmed=total_confirmed, deaths=total_deaths)
