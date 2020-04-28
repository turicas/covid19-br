import csv
import datetime
import io

from flask import Flask, make_response
from scrapy.crawler import CrawlerProcess

from .spiders.corona_pe_spider import Covid19PESpider


app = Flask(__name__)


class CustomPESpider(Covid19PESpider):
    def __init__(self, fobj, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fobj = fobj
        self.writer = None

    def write_row(self, row):
        if self.writer is None:
            self.writer = csv.DictWriter(self.fobj, fieldnames=list(row.keys()))
            self.writer.writeheader()
        self.writer.writerow(row)

    def parse(self, response):
        for row in super().parse(response):
            self.write_row(row)


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
        </ul>
      </body>
    </html>
    """


@app.route("/PE")
def pe():
    now = datetime.datetime.now()
    today = datetime.date(now.year, now.month, now.day)  # TODO: UTC-3?
    fobj = io.StringIO()
    process = CrawlerProcess(settings={})
    process.crawl(CustomPESpider, fobj=fobj)
    process.start()

    response = make_response(fobj.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=caso-pe-{today}.csv"
    response.headers["Content-type"] = "text/csv"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0")
