#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 22:56:22 2020

@author: matbit
"""

import os
import re
from urllib.parse import urljoin
from pathlib import Path

import rows
import scrapy
from rows.plugins.plugin_pdf import PyMuPDFBackend, same_column
import pandas as pd
from datetime import date



BASE_PATH = Path(__file__).parent
OUTPUT_PATH = BASE_PATH / "data" / "output"
DOWNLOAD_PATH = BASE_PATH / "data" / "download"
REGEXP_UPDATE = re.compile("Atualização .* ([0-9]{1,2}/[0-9]{1,2}/[0-9]{4}).*")


class CoronaScSpider(scrapy.Spider):
	name = "corona-sc"
	# cidades_url:
	#   chave = Nome da cidade;
	#   valor = link para o site da cidade onde divulgarao as informacoes sobre covid-19;
	cidades_url = {}
	cidades_url['Joinville'] = "https://www.joinville.sc.gov.br/publicacoes/dados-casos-coronavirus-municipio-de-joinville/"
	start_urls = cidades_url.values()
	
	# data_cities: Dicionario para armazenar as informacoes de todas as cidades do estado de SC
	data_cities = {
		"date": [],
		"state": [],
		"city": [],
		"place_type": [],
		"notified": [],
		"confirmed": [],
		"discarded": [],
		"suspect": [],
		"deaths": [],
		"notes": [],
		"source_url": [],
	}
	
	def parse(self, response):
		
		# Iterando para cada cidade que sera extraida a informacao,
		#   a cada iteracao, apenas uma cidade tera sua informacao extraindo e gravada em 'data_cities'
		for cidade in CoronaScSpider.cidades_url.keys():
			
			# data: Ira armazenar as informacoes de cada cidade por vez
			data = {}
			data["state"] = "SC"
			data["place_type"] = "city"
			data["city"] = cidade
			data["source_url"] = CoronaScSpider.cidades_url[cidade]
			
			# Inicio scrapper para a cidade de Joinville:
			if  cidade == 'Joinville':
				count = 0
				# row_tab = [0: Situacao, 1: Notificados, 2: Descartados,
				#   3: Aguardando exame, 4: Confirmados, 5: Obitos]
				for row_tab in response.xpath("//body/main/div[3]/div[1]/div[1]/div[2]/table[1]/tbody/*"):
					if count == 0:
						data["notes"] = row_tab.xpath("./th[2]/text()").extract_first()
						data["date"] = date.today()
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
					
			# elif cidade == 'Nova cidade':
			#   comece aqui o scrapper para a 'Nova cidade'
			
			self.salvar_dados(data)
			
		# Gerar o csv 'caso-sc.csv'
		self.write_csv()


	def salvar_dados(self, data_city):
		
		CoronaScSpider.data_cities["date"].append(data_city["date"])
		CoronaScSpider.data_cities["state"].append(data_city["state"])
		CoronaScSpider.data_cities["city"].append(data_city["city"])
		CoronaScSpider.data_cities["place_type"].append(data_city["place_type"])
		CoronaScSpider.data_cities["notified"].append(data_city["notified"])
		CoronaScSpider.data_cities["confirmed"].append(data_city["confirmed"])
		CoronaScSpider.data_cities["discarded"].append(data_city["discarded"])
		CoronaScSpider.data_cities["suspect"].append(data_city["suspect"])
		CoronaScSpider.data_cities["deaths"].append(data_city["deaths"])
		CoronaScSpider.data_cities["notes"].append(data_city["notes"])
		CoronaScSpider.data_cities["source_url"].append(data_city["source_url"])
		
	
	def write_csv(self):
		
		df_city_sc = pd.read_csv(DOWNLOAD_PATH / Path("all_cities_sc.csv"))
		cities_sc = df_city_sc.iloc[:].values
		
		filename = OUTPUT_PATH / Path("caso-sc.csv")
		
		# Adicionando o registro do estado SC
		CoronaScSpider.data_cities["date"].append(date.today())
		CoronaScSpider.data_cities["state"].append("SC")
		CoronaScSpider.data_cities["city"].append("")
		CoronaScSpider.data_cities["place_type"].append("state")
		CoronaScSpider.data_cities["notified"].append(sum(CoronaScSpider.data_cities["notified"]))
		CoronaScSpider.data_cities["confirmed"].append(sum(CoronaScSpider.data_cities["confirmed"]))
		CoronaScSpider.data_cities["discarded"].append(sum(CoronaScSpider.data_cities["discarded"]))
		CoronaScSpider.data_cities["suspect"].append(sum(CoronaScSpider.data_cities["suspect"]))
		CoronaScSpider.data_cities["deaths"].append(sum(CoronaScSpider.data_cities["deaths"]))
		CoronaScSpider.data_cities["notes"].append("")
		CoronaScSpider.data_cities["source_url"].append("")
		
		# Adicionando as cidades que ainda nao tiveram seus dados raspados
		for cidade in cities_sc:
			if cidade not in CoronaScSpider.data_cities["city"]:
				
				CoronaScSpider.data_cities["date"].append("")
				CoronaScSpider.data_cities["state"].append("SC")
				CoronaScSpider.data_cities["city"].append(cidade[0])
				CoronaScSpider.data_cities["place_type"].append("city")
				CoronaScSpider.data_cities["notified"].append("")
				CoronaScSpider.data_cities["confirmed"].append("")
				CoronaScSpider.data_cities["discarded"].append("")
				CoronaScSpider.data_cities["suspect"].append("")
				CoronaScSpider.data_cities["deaths"].append("")
				CoronaScSpider.data_cities["notes"].append("")
				CoronaScSpider.data_cities["source_url"].append("")
		
		
		df_out = pd.DataFrame.from_dict(CoronaScSpider.data_cities)
		
		df_out.sort_values("city")
		
		df_out.to_csv(filename, index=False)
