from scrapy.crawler import CrawlerProcess

import sys
sys.path[0] = '/'.join(sys.path[0].split('/')[:-1])

from covid19br.common.data_normalization_utils import NormalizationUtils
from covid19br.spiders.spider_ba import SpiderBA
from covid19br.spiders.spider_pr import SpiderPR

# todo -> receber crawlers a serem rodados por parâmetro (ou rodar todos se nenhum for informado)
# todo -> receber datas por parametro
start_date = '25/12/2021'
end_date = '31/12/2021'

start_date = NormalizationUtils.extract_date(start_date) if start_date else None
end_date = NormalizationUtils.extract_date(end_date) if end_date else None

# Todo -> Automatically retrieve spiders that extend the Base Class
AVAILABLE_SPIDERS = [
    SpiderBA,
    SpiderPR,
]

all_reports = {}

process = CrawlerProcess(settings={
    'USER_AGENT': (
        'Brasil.IO - Scraping para libertacao de dados da Covid 19 | Mais infos em: https://brasil.io/dataset/covid19/'
    ),
})
for spider in AVAILABLE_SPIDERS:
    reports = {}
    all_reports[spider.name] = reports
    process.crawl(spider, reports=reports, start_date=start_date, end_date=end_date)
process.start()

# todo -> save results in csv instead of printing them
print(
    '\n'
    '\n---------'
    '\nREPORTS'
    '\n---------'
)
for state, reports in all_reports.items():
    print(f'{state}:')
    for date, report in reports.items():
        print(f'- ({date}) {report}')
