import io
import multiprocessing

from scrapy.crawler import CrawlerProcess

from .spider_ce import Covid19CESpider
from .spider_es import Covid19ESSpider
from .spider_pe import Covid19PESpider
from .spider_pr import Covid19PRSpider
from .spider_rn import Covid19RNSpider
from .spider_rr import Covid19RRSpider


SPIDERS = [
    Covid19CESpider,
    Covid19ESSpider,
    Covid19PESpider,
    Covid19PRSpider,
    Covid19RNSpider,
    Covid19RRSpider,
]
STATE_SPIDERS = {SpiderClass.name: SpiderClass for SpiderClass in SPIDERS}
# TODO: do autodiscovery from base class' subclasses


def execute_spider_worker(SpiderClass):
    report_fobj, case_fobj = io.StringIO(), io.StringIO()
    try:
        process = CrawlerProcess(settings={})
        process.crawl(SpiderClass, report_fobj=report_fobj, case_fobj=case_fobj)
        process.start()
    except Exception as exp:
        import traceback
        return "error", traceback.format_exc()
    else:
        report_fobj.seek(0)
        case_fobj.seek(0)
        return "ok", (report_fobj, case_fobj)


def run_state_spider(state, subprocess=True):
    state = str(state or "").upper().strip()
    if state not in STATE_SPIDERS:
        raise ValueError(f"Spider for state {repr(state)} not found.")

    SpiderClass = STATE_SPIDERS[state]
    if subprocess:
        with multiprocessing.Pool(1) as pool:
            return pool.map(execute_spider_worker, [SpiderClass])[0]
    else:
        return execute_spider_worker(SpiderClass)
