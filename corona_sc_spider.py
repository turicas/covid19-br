#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 22:56:22 2020

@author: matbit
"""

from pathlib import Path
import rows
import scrapy
from datetime import date

BASE_PATH = Path(__file__).parent
OUTPUT_PATH = BASE_PATH / "data" / "output"
DATA_PATH = BASE_PATH / "data"


class CoronaScSpider(scrapy.Spider):
	name = "corona-sc"

	def __init__(self, *args, **kwargs):
		super(CoronaScSpider, self).__init__(*args, **kwargs)
		self.cidades_url = {}
		# cidades_url:
		#   chave = Nome da cidade;
		#   valor = link para o site da cidade onde divulgarao as informacoes sobre covid-19;
		self.cidades_url['Joinville'] = "https://www.joinville.sc.gov.br/publicacoes/dados-casos-coronavirus-municipio-de-joinville/"
		# Adicionar mais cidades com suas URLs aqui:
		# self.cidades_url['Nome Cidade'] = "url_para_dados_covid-19_da_cidade"

		# data_cities: lista de dicionarios para armazenar as informacoes das cidades do estado de SC
		self.data_cities = []

		self.start_urls = self.cidades_url.values()

		cities_br = rows.import_from_csv(DATA_PATH / "populacao-estimada-2019.csv")

		self.cities_sc_ibge = [row for row in cities_br if row.uf == "SC"]


	def parse(self, response):
		# data: Dicionario para armazenar as informacoes de cada cidade por vez
		data = {}
		data["state"] = "SC"


		# Inicio scrapper para a cidade de Joinville:
		if  response.url == self.cidades_url['Joinville']:
			cidade = 'Joinville'

			data["city"] = cidade
			data["place_type"] = "city"
			data["source_url"] = response.url

			joinville_ibge = [row for row in self.cities_sc_ibge if row.municipio == 'Joinville'][0]

			data["estimated_population_2019"] = int(joinville_ibge.populacao_estimada)
			data["city_ibge_code"] = str(joinville_ibge.codigo_municipio)

			response_path_common = "//body/main/div[3]/div[1]/div[1]/div[2]/table[2]/tbody/tr[2]/"

			date_hour = response.xpath(response_path_common + "td[1]/text()").extract_first()

			update_date = date_hour.split(" ")[0]
			update_date = update_date.split("/")[::-1]
			update_date = "-".join(update_date)

			data["date"] = update_date
			data["notified"] = int(response.xpath(response_path_common + "td[2]/text()").extract_first())
			data["discarded"] = int(response.xpath(response_path_common + "td[3]/text()").extract_first())
			data["suspect"] = int(response.xpath(response_path_common + "td[4]/text()").extract_first())
			data["confirmed"] = int(response.xpath(response_path_common + "td[5]/text()").extract_first())
			recuperados = int(response.xpath(response_path_common + "td[6]/text()").extract_first())
			data["deaths"] = int(response.xpath(response_path_common + "td[7]/text()").extract_first())
			data["notes"] = "Ultima atualizacao em: " + date_hour

			data["confirmed_per_100k_inhabitants"] = (100000.0 * data["confirmed"]) / data["estimated_population_2019"]
			data["death_rate"] = float(data["deaths"]) / data["confirmed"]


		# elif response.url == self.cidades_url['Nova Cidade']:
		#   comece aqui o scrapper para a 'Nova Cidade'


		self.data_cities.append(data)

		# Gerar o csv 'caso-sc.csv'
		self.write_csv()


	def write_csv(self):

		filename = OUTPUT_PATH / Path("caso-sc.csv")

		# Adicionando a 'row' do estado de SC
		data = {}
		data["date"] = date.today()
		data["state"] = "SC"
		data["city"] = ""
		data["place_type"] = "state"
		data["notified"] = sum([self.data_cities[i]["notified"] for i in range(len(self.data_cities))])
		data["confirmed"] = sum([self.data_cities[i]["confirmed"] for i in range(len(self.data_cities))])
		data["discarded"] = sum([self.data_cities[i]["discarded"] for i in range(len(self.data_cities))])
		data["suspect"] = sum([self.data_cities[i]["suspect"] for i in range(len(self.data_cities))])
		data["deaths"] = sum([self.data_cities[i]["deaths"] for i in range(len(self.data_cities))])

		data["city_ibge_code"] = ""
		data["estimated_population_2019"] = sum([self.data_cities[i]["estimated_population_2019"] for i in range(len(self.data_cities))])
		data["confirmed_per_100k_inhabitants"] = sum([self.data_cities[i]["confirmed_per_100k_inhabitants"] for i in range(len(self.data_cities))])
		data["death_rate"] = sum([self.data_cities[i]["death_rate"] for i in range(len(self.data_cities))]) / len(self.data_cities)
		data["notes"] = ""
		data["source_url"] = ""
		self.data_cities.append(data)

		# Adicionando as cidades que nao foram parseadas ainda
		for each_city in self.cities_sc_ibge:
			if each_city.municipio not in self.cidades_url.keys():
				data = {}
				data["date"] = ""
				data["state"] = "SC"
				data["city"] = each_city.municipio
				data["place_type"] = "city"
				data["notified"] = ""
				data["confirmed"] = ""
				data["discarded"] = ""
				data["suspect"] = ""
				data["deaths"] = ""
				data["notes"] = ""
				data["city_ibge_code"] = ""
				data["estimated_population_2019"] = ""
				data["confirmed_per_100k_inhabitants"] = ""
				data["death_rate"] = ""
				data["source_url"] = ""
				self.data_cities.append(data)


		# keyorder = ['date', 'state', 'city', 'place_type', 'notified', 'confirmed', 'discarded', 'suspect', 'deaths', 'notes', 'city_ibge_code', 'estimated_population_2019', 'confirmed_per_100k_inhabitants', 'death_rate', 'source_url']
		#
		# data_cities_ordered = []
		# for d in self.data_cities:
		# 	data_cities_ordered.append(sorted(d.items(), key=lambda i:keyorder.index(i[0])))

		rows_data = rows.import_from_dicts(self.data_cities)

		rows_data.order_by("city")

		rows.export_to_csv(rows_data, filename)
