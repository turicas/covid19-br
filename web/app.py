import csv
import datetime
import io

from flask import Flask, make_response
from scrapy.crawler import CrawlerProcess

from .spiders.spider_es import Covid19ESSpider
from .spiders.spider_pe import Covid19PESpider
from .spiders.spider_pr import Covid19PRSpider
from .spiders.spider_rn import Covid19RNSpider
from .spiders.spider_rr import Covid19RRSpider

SPIDERS = [Covid19ESSpider, Covid19PESpider, Covid19PRSpider, Covid19RRSpider, Covid19RNSpider]
STATE_SPIDERS = {SpiderClass.name: SpiderClass for SpiderClass in SPIDERS}


app = Flask(__name__)


@app.route("/")
def index():
    spider_links = "\n".join(
        f'<li> <a href="/{state}">{state}</a> </li>' for state in STATE_SPIDERS.keys()
    )
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Brasil.IO COVID-19 Spiders</title>
      </head>
      <body>
        <ul>
          {spider_links}
        </ul>
      </body>
    </html>
    """


def get_spider_response(SpiderClass, state):
    report_fobj, case_fobj = io.StringIO(), io.StringIO()
    process = CrawlerProcess(settings={})
    process.crawl(SpiderClass, report_fobj=report_fobj, case_fobj=case_fobj)
    process.start()

    report_fobj.seek(0)
    reports = list(csv.DictReader(report_fobj))
    date = reports[0]["date"]
    # TODO: do something with reports

    response = make_response(case_fobj.getvalue())
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename=caso-{state}-{date}.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route("/<state>")
def get_state_csv(state):
    state = state.upper().strip()
    if state not in STATE_SPIDERS:
        return "State not found", 404

    return get_spider_response(STATE_SPIDERS[state], state)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
