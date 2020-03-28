#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 22:56:22 2020

@author: matbit
"""

import re
from pathlib import Path

import rows
import scrapy
from datetime import date



BASE_PATH = Path(__file__).parent
OUTPUT_PATH = BASE_PATH / "data" / "output"
DATA_PATH = BASE_PATH / "data"
REGEXP_UPDATE = re.compile("Atualização .* ([0-9]{1,2}/[0-9]{1,2}/[0-9]{4}).*")


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

		self.cities_br = rows.import_from_csv(DATA_PATH / "populacao-estimada-2019.csv")


	def parse(self, response):
		# data: Dicionario para armazenar as informacoes de cada cidade por vez
		data = {}
		data["date"] = date.today()
		data["state"] = "SC"
		

		# Inicio scrapper para a cidade de Joinville:
		if  response.url == self.cidades_url['Joinville']:
			cidade = 'Joinville'

			data["city"] = cidade
			data["place_type"] = "city"

			count = 0
			note = ""
			# row_tab = [0: Situacao, 1: Notificados, 2: Descartados,
			#   3: Aguardando exame, 4: Confirmados, 5: Obitos]
			for row_tab in response.xpath("//body/main/div[3]/div[1]/div[1]/div[2]/table[1]/tbody/*"):
				if count == 0:
					note = row_tab.xpath("./th[2]/text()").extract_first()
				elif count == 1:
					data["notified"] = int(row_tab.xpath("./td[2]/text()").extract_first())
				elif count == 2:
					data["discarded"] = int(row_tab.xpath("./td[2]/text()").extract_first())
				elif count == 3:
					data["suspect"] = int(row_tab.xpath("./td[2]/text()").extract_first())
				elif count == 4:
					data["confirmed"] = int(row_tab.xpath("./td[2]/text()").extract_first())
				elif count == 5:
					data["deaths"] = int(row_tab.xpath("./td[2]/text()").extract_first())
				count += 1
				
			data["notes"] = note
			data["source_url"] = response.url

		# elif response.url == self.cidades_url['Nova Cidade']:
		#   comece aqui o scrapper para a 'Nova Cidade'


		self.data_cities.append(data)

		# Gerar o csv 'caso-sc.csv'
		self.write_csv()


	def write_csv(self):
		
		filename = OUTPUT_PATH / Path("caso-sc.csv")

		cities_sc = [row for row in self.cities_br
		             if row.uf == "SC"]
		
		# cities_scraped = rows.import_from_dicts(self.data_cities)
		
		# print(cities_sc["municipio"])
		
		# Adicionando a 'row' do estado de SC
		data = {}
		data["date"] = date.today()
		data["state"] = "SC"
		data["city"] = ""
		data["place_type"] = "state"
		data["notified"] = 0 #sum(self.data_cities[0]["notified"])
		data["confirmed"] = 0 #sum(self.data_cities[0]["confirmed"])
		data["discarded"] = 0 #sum(self.data_cities[0]["discarded"])
		data["suspect"] = 0 #sum(self.data_cities[0]["suspect"])
		data["deaths"] = 0 #sum(self.data_cities[0]["deaths"])
		data["notes"] = ""
		data["source_url"] = ""
		self.data_cities.append(data)
		
		# Adicionando as cidades que nao foram parseadas ainda
		for each_city in cities_sc:
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
				data["source_url"] = ""
				self.data_cities.append(data)
		
		
		rows.export_to_csv(rows.import_from_dicts(self.data_cities), filename)

