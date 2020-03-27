import csv
import datetime
import hashlib
import io
import os

import rows
import scrapy
from html2text import HTML2Text

import rocketchat


URL_LIST_URL = "https://docs.google.com/spreadsheets/d/1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI/export?format=csv&id=1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI&gid=0"
HASH_LIST_URL = "https://data.brasil.io/dataset/covid19/url-hash.csv"


def sha512sum(content):
    return hashlib.sha512(content).hexdigest()


def last_check_str(value):
    if value:
        return f" A última verificação (antes dessa) foi feita em `{value}`."
    else:
        return " Eu ainda não tinha verificado essa URL."


class URLCheckerSpider(scrapy.Spider):
    name = "url-checker"
    start_urls = [HASH_LIST_URL]
    custom_settings = {"DNS_TIMEOUT": 10, "DOWNLOAD_TIMEOUT": 10}

    def __init__(self, output_filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_filename = output_filename
        self.urls_to_check, self.result = set(), []
        self.chat = rocketchat.RocketChat(os.environ["ROCKETCHAT_BASE_URL"])
        self.chat.user_id = os.environ["ROCKETCHAT_USER_ID"]
        self.chat.auth_token = os.environ["ROCKETCHAT_AUTH_TOKEN"]

    def parse(self, response):
        url_table = rows.import_from_csv(io.BytesIO(response.body), encoding="utf-8")
        self.URLInfo = url_table.Row
        self.url_hashes = {row.url: row for row in url_table}
        yield scrapy.Request(URL_LIST_URL, callback=self.parse_url_list)

    def parse_url_list(self, response):
        table = rows.import_from_csv(io.BytesIO(response.body), encoding="utf-8")
        for row in table:
            url_list = row.boletins_da_secretaria_estadual_de_saude
            if not (url_list or "").strip():
                continue
            for url in url_list.split(","):
                url = url.strip()
                meta = {"state": row.uf, "url": url, "channel": row.canal}
                self.urls_to_check.add(url)
                yield scrapy.Request(
                    url,
                    callback=self.parse_url,
                    meta={"row": meta},
                    errback=self.handle_failure,
                    dont_filter=True,
                )

    def notify(self, channel, message):
        self.chat.send_message(channel, message)

    def url_info(self, url):
        return self.url_hashes.get(
            url, self.URLInfo(url=url, last_check_datetime=None, sha512sum=None)
        )

    def handle_failure(self, failure):
        meta = failure.request.meta["row"]
        url = meta["url"]
        url_info = self.url_info(url)
        url_info = url_info._asdict()
        url_info["sha512sum"] = "ERROR"
        url_info["last_check_datetime"] = datetime.datetime.now()
        self.urls_to_check.remove(url)
        self.result.append(url_info)
        if hasattr(failure.value, "response") and hasattr(
            failure.value.response, "status"
        ):
            failure_str = f"(HTTP {failure.value.response.status}) {failure.value}"
        else:
            failure_str = str(failure.value)
        self.notify(
            meta["channel"],
            (
                f"@all tentei checar o [site da SES de `{meta['state']}`]({url}) "
                f"mas aconteceu um erro! =/ (`{failure_str}`)."
            )
            + last_check_str(url_info["last_check_datetime"]),
        )

    def parse_url(self, response):
        meta = response.meta["row"]
        url = meta["url"]
        url_info = self.url_info(url)
        now = datetime.datetime.now()
        html_parser = HTML2Text()
        html_parser.ignore_links = True
        html_parser.ignore_images = True
        text = html_parser.handle(response.body_as_unicode())
        content_hash = sha512sum(text.encode("utf-8"))
        if content_hash != url_info.sha512sum:
            self.notify(
                meta["channel"],
                f"@all detectei uma alteração no [site da SES de `{meta['state']}`]({url})."
                + last_check_str(url_info.last_check_datetime),
            )
        self.urls_to_check.remove(url)
        url_info = url_info._asdict()
        url_info["last_check_datetime"] = now
        url_info["sha512sum"] = content_hash
        self.result.append(url_info)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(
            spider.spider_closed, signal=scrapy.signals.spider_closed
        )
        return spider

    def spider_closed(self, spider):
        writer = rows.utils.CsvLazyDictWriter(self.output_filename)
        for row in self.result:
            writer.writerow(row)
