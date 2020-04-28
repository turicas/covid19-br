import csv
import datetime
import io

from flask import Flask, make_response
from scrapy.crawler import CrawlerProcess

from .spiders.spider_pe import Covid19PESpider
from .spiders.spider_rr import Covid19RRSpider


app = Flask(__name__)

@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Brasil.IO COVID-19 Spiders</title>
      </head>
      <body>
        <ul>
          <li> <a href="/PE">Pernambuco</a> </li>
          <li> <a href="/RR">Roraima</a> </li>
        </ul>
      </body>
    </html>
    """

def get_spider_response(SpiderClass, state):
    now = datetime.datetime.now()
    today = datetime.date(now.year, now.month, now.day)  # TODO: UTC-3?
    fobj = io.StringIO()
    process = CrawlerProcess(settings={})
    process.crawl(SpiderClass, fobj=fobj)
    process.start()

    response = make_response(fobj.getvalue())
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename=caso-{state}-{today}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route("/PE")
def pe():
    return get_spider_response(Covid19PESpider, "PE")

@app.route("/RR")
def rr():
    return get_spider_response(Covid19RRSpider, "RR")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
