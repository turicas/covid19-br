import numpy as np
import pandas as pd
import requests
from datetime import datetime
from urllib.request import urlopen
from bs4 import BeautifulSoup

#Definição manual do Dia 1 no ES
dia1_es = '2020-02-28'

#Colocando a data atual como o último dia, já que ainda não temos um último dia definido
diaUltimo = datetime.today().strftime("%Y-%m-%d")

#Método para fazer a diferença entre a data atual e o dia 1, este valor é usado para definir o range de pesquisa de boletins
def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)

#Definindo a quantidade de dias para buscar os boletins
dias = days_between(dia1_es, diaUltimo)

list_rows = []

def preenche_es_dia_1_a_4(list_rows):
    #Inclusão manual do dia 1 pois está em texto corrido
    dia1_es_data = ["2020-02-28","ES","","state", np.nan, np.nan, np.nan, 5, np.nan, "Sem transmissão local", "https://coronavirus.es.gov.br/Not%C3%ADcia/espirito-santo-registra-cinco-casos-suspeitos-do-covid-19"]
    list_rows.append(dia1_es_data)

    #Inclusão manual do dia 2 pois está em texto corrido
    dia2_es_data = ["2020-02-29","ES","","state", np.nan, np.nan, np.nan, 6, np.nan, "Sem transmissão local", "https://coronavirus.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-2o-boletim-de-covid-19"]
    list_rows.append(dia2_es_data)

    #Inclusão manual do dia 3 pois está em texto corrido
    dia3_es_data = ["2020-03-01","ES","","state", np.nan, np.nan, 5, 1, np.nan, "Sem transmissão local", "https://coronavirus.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-3o-boletim-de-covid-19"]
    list_rows.append(dia3_es_data)

    #Inclusão manual do dia 4 pois está em texto corrido
    dia4_es_data = ["2020-03-02","ES","","state", np.nan, np.nan, np.nan, 6, np.nan, "Sem transmissão local","https://coronavirus.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-4o-boletim-de-covid-19"]
    list_rows.append(dia4_es_data)


def preenche_es_dia_5_a_20(list_rows):
    #url do dia 5 começa com 5o - 2º Boletim  - https://coronavirus.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-5o-boletim-de-covid-19
    #contando até o dia 21, pois a partir daí a tabela retorna a cidade

    dias_boletins = range(5, 21) # até o dia 2020-03-18

    for dia in dias_boletins:
        # gerando URLs
        url_dia = "https://coronavirus.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-{}o-boletim-de-covid-19".format(dia)
        url_dia_alternativa = "https://saude.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-{}o-boletim-de-covid-19".format(dia)
        
        response = requests.get(url_dia_alternativa)
        if (response.status_code == 200):
            html_doc = response.text
            soup = BeautifulSoup(html_doc, 'html.parser')
            print(url_dia_alternativa)

            #lendo a data do boletim
            div_data = soup.find("div", class_="published").get_text().split(" ")[0]
            div_data = div_data.split("/")
            div_data = '{:%Y-%m-%d}'.format(datetime(int(div_data[2]), int(div_data[1]), int(div_data[0])))
            print(div_data)

            #Lendo a tabela da URL
            table = soup.find("table")
            countRow = 0
            list_keys = []  
            list_dia = []

            for row in table.find_all("tr"):    
                list_total = []

                for col in row.find_all("td"):            
                    if countRow == 0:
                        list_keys.append(col.get_text().strip('\n').replace("\n"," ").replace("\xa0"," ").replace("Casos ","").replace("em ","").replace(" ","").lower())
                    else:
                        list_total.append(col.get_text().strip('\n').replace("\n"," ").replace("\xa0"," "))

                countRow += 1

            #Unindo a lista de chaves da tabela com a linha do total
            res = dict(zip(list_keys, list_total)) 

            print(res["confirmados"])
            confirmados = np.nan if res["confirmados"] == 0 else res["confirmados"]
            notificados = np.nan if res["notificados"] == 0 else res["notificados"]
            descartados = np.nan if res["descartados"] == 0 else res["descartados"]
            suspeitos = np.nan if res["investigação"] == 0 else res["investigação"]
            mortes = np.nan

            list_dia = [div_data, "ES","","state", notificados, confirmados, descartados, suspeitos, mortes, "", url_dia_alternativa]
            list_rows.append(list_dia)

            print("")
            print("*****")
        

def preenche_es_dia_21_a_23(list_rows):
    #ALTERANDO PARA PEGAR O DETALHAMENTO DE MUNICIPIOS
    #depois ler do range 21 ao último dia
    dias_boletins = range(21, 24)

    for dia in dias_boletins:
        # gerando URLs
        url_dia = "https://coronavirus.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-{}o-boletim-de-covid-19".format(dia)
        url_dia_alternativa = "https://saude.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-{}o-boletim-de-covid-19".format(dia)
        
        response = requests.get(url_dia_alternativa)
        if (response.status_code == 200):
            html_doc = response.text
            soup = BeautifulSoup(html_doc, 'html.parser')
            print(url_dia_alternativa)

            #lendo a data do boletim
            div_data = soup.find("div", class_="published").get_text().split(" ")[0]
            div_data = div_data.split("/")
            div_data = '{:%Y-%m-%d}'.format(datetime(int(div_data[2]), int(div_data[1]), int(div_data[0])))
            print(div_data)

            #Lendo a tabela da URL
            table = soup.find("table")
            countRow = 0
            list_keys = []  
            list_dia = []
            list_total = []

            for row in table.find_all("tr"):            
                list_municipio = []

                for col in row.find_all("td"):            
                    if countRow == 0:
                        list_keys.append(col.get_text().strip('\n').replace("\n"," ").replace("\xa0"," ").replace("Casos ","").replace("em ","").replace(" ","").lower())
                    else:
                        list_municipio.append(col.get_text().strip('\n').replace("\n"," ").replace("\xa0"," "))
                
                if countRow > 0:
                    list_total.append(list_municipio)
                countRow += 1            
                
            
            
            for municipio in list_total:
                if (len(municipio) > 5):
                    if (municipio[0].find("TOTAL") != -1):
                        res = dict(zip(list_keys[-5:], municipio)) 
                        nome_cidade = ""
                        place_type = "state"
                    else:
                        cidade = municipio[-5:]
                        #Unindo a lista de chaves da tabela com a linha do total
                        res = dict(zip(list_keys[-5:], cidade)) 

                        nome_cidade = cidade[0]
                        place_type = "city"
                else:
                    res = dict(zip(list_keys[-5:], municipio)) 
                    nome_cidade = municipio[0]
                    place_type = "city"
                        
                confirmados = np.nan if res["confirmados"] == 0 else res["confirmados"]
                notificados = np.nan if res["notificados"] == 0 else res["notificados"]
                descartados = np.nan if res["descartados"] == 0 else res["descartados"]
                suspeitos = np.nan if res["suspeitos"] == 0 else res["suspeitos"]
                mortes = np.nan

                list_dia = [div_data, "ES",nome_cidade,place_type, notificados, confirmados, descartados, suspeitos, mortes, "", url_dia_alternativa]                
                list_rows.append(list_dia)       

            print("*****")
            print("")


def preenche_es_dia_24_ao_fim(lis_rows):
    dias_boletins = range(24, dias+2)

    for dia in dias_boletins:
        print(dia)
        # gerando URLs
        url_dia = "https://coronavirus.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-{}o-boletim-de-covid-19".format(dia)
        url_dia_alternativa = "https://saude.es.gov.br/Not%C3%ADcia/secretaria-da-saude-divulga-{}o-boletim-de-covid-19".format(dia)

        response = requests.get(url_dia_alternativa)
        if (response.status_code == 200):
            html_doc = response.text
            soup = BeautifulSoup(html_doc, 'html.parser')
            print(url_dia_alternativa)

            #lendo a data do boletim
            div_data = soup.find("div", class_="published").get_text().split(" ")[0]
            div_data = div_data.split("/")
            div_data = '{:%Y-%m-%d}'.format(datetime(int(div_data[2]), int(div_data[1]), int(div_data[0])))
            print(div_data)

            #Lendo a tabela da URL
            table = soup.find("table")
            countRow = 0
            list_keys = []  
            list_dia = []
            list_total = []
            
            for row in table.find_all("tr"):            
                list_municipio = []            

                for col in row.find_all("td"):
                    if countRow == 1:
                        list_keys.append(col.get_text().strip('\n').replace("\n"," ").replace("\xa0"," ").replace("Caso ","").replace(" ","").lower())
                    else:
                        list_municipio.append(col.get_text().strip('\n').replace("\n"," ").replace("\xa0"," "))

                if countRow > 0:
                    list_total.append(list_municipio)
                countRow += 1   

            for municipio in list_total:
                if (len(municipio) > 1):              
                    if (municipio[0] == ''):
                        pass
                    elif (municipio[1].find("Caso") != -1):
                        pass
                    else:
                        if (municipio[0].find("Total Geral") != -1):
                            cidade = municipio
                            res = dict(zip(list_keys[-5:], cidade)) 
                            
                            nome_cidade = ""
                            place_type = "state"
                        else:
                            cidade = municipio
                            #Unindo a lista de chaves da tabela com a linha do total
                            res = dict(zip(list_keys[-5:], cidade)) 

                            nome_cidade = cidade[0]
                            place_type = "city"

                        confirmados = np.nan if res["confirmado"] == 0 else res["confirmado"]
                        notificado = np.nan
                        descartados = np.nan if res["descartado"] == 0 else res["descartado"]
                        suspeitos = np.nan if res["suspeito"] == 0 else res["suspeito"]
                        mortes = np.nan

                        list_dia = [div_data, "ES",nome_cidade,place_type, notificado, confirmados, descartados, suspeitos, mortes, "", url_dia_alternativa]                
                        list_rows.append(list_dia)       

            print("*****")
            print("")


preenche_es_dia_1_a_4(list_rows)
preenche_es_dia_5_a_20(list_rows)
preenche_es_dia_21_a_23(list_rows)
preenche_es_dia_24_ao_fim(list_rows)

covid_es = pd.DataFrame(list_rows, columns=['date','state','city','place_type','notified','confirmed','discarded','suspect','deaths','notes','source_url'])
print(covid_es)
covid_es.to_csv("data/output/boletins_es.csv", encoding='utf-8')