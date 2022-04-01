import csv
import io

import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from covid19br.common.base_spider import BaseCovid19Spider
from covid19br.common.constants import ReportQuality, State
from covid19br.common.models.bulletin_models import CountyBulletinModel, StateTotalBulletinModel


class SpiderRJ(BaseCovid19Spider):
    name = State.RJ.value
    state = State.RJ
    information_delay_in_days = 0
    report_qualities = [ReportQuality.COUNTY_BULLETINS]
    start_urls = ["http://sistemas.saude.rj.gov.br/tabnetbd/dhx.exe?covid19/tf_covid_brasil.def"]

    def pre_init(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.requested_dates = list(self.requested_dates)

    def parse(self, response, **kwargs):
        self.driver.get(response.url)
        # Select Município
        self.driver.find_element_by_xpath('//*[@value="Município|municipio"]').click()

        # Select Óbitos and Confirmados
        element = self.driver.find_element_by_xpath('//*[@value="Obitos confirmados|obitosnovos"]')
        ActionChains(self.driver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform()

        # Open states menu
        self.driver.find_element_by_xpath('//*[@id="fig4"]').click()

        # Select RJ state
        element = self.driver.find_element_by_xpath('//*/option[@value="RJ|RJ,|2"]')
        ActionChains(self.driver).click(element).perform()

        # Click dates menu
        self.driver.find_element_by_xpath('//*[@id="fig1"]').click()

        for date in self.requested_dates:
            # Select start date
            element = self.driver.find_element_by_xpath(
                f'//*/select[2]/option[@value="2020-01-01|2020-01-01|10"]'
            )
            ActionChains(self.driver).click(element).perform()
            
            # Select end date
            element = self.driver.find_element_by_xpath(
                f'//*/select[2]/option[@value="{f"{str(date)}|{str(date)}|10"}"]'
            )
            ActionChains(self.driver).key_down(Keys.SHIFT).click(element).perform()

            # Click button mostrar
            self.driver.find_element_by_xpath("//*/form/div[2]/div[2]/div[3]/input[1]").click()
            self.driver.switch_to.window(self.driver.window_handles[1])

            # Get url from button download csv
            url_csv = self.driver.find_element_by_xpath("//*/div[3]/table/tbody/tr/td[2]/a").get_attribute("href")

            yield scrapy.Request(
                url_csv,
                callback=self.parse_csv,
                cb_kwargs={"date": date},
            )

            # Close tab
            self.driver.close()

            # Go back to main tab
            self.driver.switch_to.window(self.driver.window_handles[0])

        self.driver.quit()

    def parse_csv(self, response, date):
        report = csv.DictReader(io.StringIO(response.body.decode("iso-8859-15")), delimiter=";")

        for row in report:
            if row["Município"].lower() == "total":
                bulletin = StateTotalBulletinModel(
                    date=date,
                    state=self.state,
                    confirmed_cases=row["Casos confirmados"],
                    deaths=row["Obitos confirmados"],
                    source=response.request.url,
                )
            else:
                bulletin = CountyBulletinModel(
                    date=date,
                    state=self.state,
                    city=row["Município"],
                    confirmed_cases=row["Casos confirmados"],
                    deaths=row["Obitos confirmados"],
                    source=response.request.url,
                )
            self.add_new_bulletin_to_report(bulletin, date)
