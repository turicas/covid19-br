import string
import scrapy
from datetime import datetime, timedelta



class MGSpider(BaseCovid19Spider):
    name = "MG"

    def start_requests(self):
        # Get the current day
        current_day = datetime.today().strftime('%d.%m.%Y')
        urls = [
            f'https://saude.mg.gov.br/images/noticias_e_eventos/000_2020/Boletins_Corona/{current_day}_Boletim_epidemiologico_COVID-19_MG.pdf',
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        current_day = datetime.today().strftime('%d.%m.%Y')
        page = response.url.split("/")[-2]
        filename = f'{current_day}_{page}.pdf'
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Opened file %s' % filename)

        return self.parse_pdf(filename)

    def parse_pdf(self, file_path):
        df = PyMuPDFBackend(file_path)

        it = df.objects()

        obitos_conf = 0
        obitos_desc = 0
        obitos_inv = 0
        total = 0

        dicts = []

        for i in it:
            for j in range(len(i)):
                if i[j].text.rstrip() == '(CASOS + ÓBITOS)':
                    general_lst = []
                    for k in range(1, 5):
                        j += 1
                        general_lst.append(int(i[j].text.rstrip()
                                    .translate(str.maketrans('', '', string.punctuation))))

                    obitos_conf, obitos_desc, obitos_inv, total = general_lst
                    # Add the state entry
                    dicts.append({
                        'city': None,
                        'date': current_day,
                        'state': 'MG',
                        'place_type': 'state',
                        'confirmed': total,
                        'deaths': obitos_conf
                        })
                # Check for the cue the table of cities will start
                if (i[j].text.rstrip() == f'N={obitos_conf}') and (i[j+1].text.rstrip() == 'residência'):
                    # Update the j
                    j += 2
                    while j < len(i):
                        # Here is where the cities will start, but first check if it is not the end
                        if i[j].text.rstrip().split(' ')[0] == "Municípios":
                            # This is the end. Just return
                            break
                        # Check if it is not a city name
                        elif i[j].text.rstrip().split(' ')[0].lower() == 'outro':
                            j+=1
                            pass
                        elif i[j].text.rstrip().split(' ')[0].lower() == 'em':
                            j+=1
                            pass
                        else:
                            # It is a city that needs to be added
                            name = i[j].text.rstrip()
                            j+=1
                            # There may be some missing -, so check if the type is right
                            if i[j].text.rstrip()[0].isalpha():
                                confirmed = 0
                                deaths = 0
                                # Add it to the list
                                dicts.append({
                                    'city': name,
                                    'date': current_day,
                                    'state': 'MG',
                                    'place_type': 'city',
                                    'confirmed': confirmed,
                                    'deaths': deaths
                                    })
                                # Go to the next j. No need to update
                            else:
                                confirmed = 0 if i[j].text.rstrip() == '-' else int(i[j].text.rstrip())
                                j+=1
                                # Check if it is not a new city
                                if i[j].text.rstrip()[0].isalpha():
                                    deaths = 0
                                    # Add it to the list
                                    dicts.append({
                                        'city': name,
                                        'date': current_day,
                                        'state': 'MG',
                                        'place_type': 'city',
                                        'confirmed': confirmed,
                                        'deaths': deaths
                                        })
                                else:
                                    deaths = 0 if i[j].text.rstrip() == '-' else int(i[j].text.rstrip())
                                    j+=1
                                    # Add it to the list
                                    dicts.append({
                                        'city': name,
                                        'date': current_day,
                                        'state': 'MG',
                                        'place_type': 'city',
                                        'confirmed': confirmed,
                                        'deaths': deaths
                                        })

        # Yield the result
        for d in dicts:
            yield {
                "city": d['city'],
                "confirmed": d['confirmed'],
                "date": d['date'],
                "deaths": d['deaths'],
                "place_type": d['place_type'],
                "state": d['state'],
            }