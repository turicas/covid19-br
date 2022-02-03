import argparse
import os
import sys
import rows
from scrapy.crawler import CrawlerProcess

sys.path[0] = '/'.join(sys.path[0].split('/')[:-1])

from covid19br.common.data_normalization_utils import NormalizationUtils
from covid19br.spiders.spider_ba import SpiderBA
from covid19br.spiders.spider_ce import SpiderCE
from covid19br.spiders.spider_pr import SpiderPR
from covid19br.spiders.spider_sp import SpiderSP
from covid19br.spiders.spider_to import SpiderTO

# Todo -> Automatically retrieve spiders that extend the Base Class
AVAILABLE_SPIDERS = [
    SpiderBA,
    SpiderCE,
    SpiderPR,
    SpiderSP,
    SpiderTO,
]


def display_available_spiders():
    print("Available spiders:")
    for spider in AVAILABLE_SPIDERS:
        print(f"- {spider.name}")


def get_spiders_to_run(filter_states) -> list:
    if not filter_states:
        return AVAILABLE_SPIDERS
    return [spider for spider in AVAILABLE_SPIDERS if spider.name in filter_states]


def build_date_parameters(start_date=None, end_date=None, dates_range=None) -> dict:
    if dates_range:
        return {
            "dates_range": [NormalizationUtils.extract_date(date_) for date_ in dates_range.split(",")]
        }
    params = {}
    if start_date:
        params["start_date"] = NormalizationUtils.extract_date(start_date)
    if end_date:
        params["end_date"] = NormalizationUtils.extract_date(end_date)
    if start_date and end_date and params["start_date"] > params["end_date"]:
        raise ValueError("BAD PARAMETER: end_date should be greater than start_date.")
    return params


def display_results(results):
    print(
        '\n'
        '\n---------'
        '\nREPORTS'
        '\n---------'
    )
    for state, reports_by_date in results.items():
        print(f'{state}:')
        if not reports_by_date:
            print("- No report found")
            continue
        for date in sorted(reports_by_date):
            print(f'- ({date}) {reports_by_date[date]}')


def create_folder_if_doesnt_exist(filename):
    *path_fragments, _csv_name = filename.split("/")
    current_path = os.getcwd()
    if not path_fragments or os.path.exists(current_path + "/".join(path_fragments)):
        return
    for path_fragment in path_fragments:
        current_path = f"{current_path}/{path_fragment}"
        if not os.path.exists(current_path):
            os.makedirs(current_path)


def save_results_in_csv(results, filename_pattern):
    print(
        '\n'
        '\n---------------'
        '\nSAVING REPORTS'
        '\n---------------'
    )
    for state, reports_by_date in results.items():
        if not reports_by_date:
            print(f'No report found for {state} - skipping...')
            continue
        for date, report in reports_by_date.items():
            filename = filename_pattern.format(date=date, state=report.state.value)
            create_folder_if_doesnt_exist(filename)
            print(f'Formatting and saving file {filename}...')
            writer = rows.utils.CsvLazyDictWriter(filename)
            for row in report.to_csv_rows():
                writer.writerow(row)
            writer.close()


parser = argparse.ArgumentParser(
    description='Runs spiders to get covid-19 data for one or more states in specified dates.'
)
parser.add_argument(
    "--available_spiders",
    help='list the names of all available spiders',
    action='store_true',
)
parser.add_argument(
    "--start_date",
    help='Date in the format dd/mm/yyyy. '
         'The spiders only gather data provided after this date (open interval). '
         'Default is today (when dates_range is not set)'
)
parser.add_argument(
    "--end_date",
    help='Date in the format dd/mm/yyyy. '
         'The spiders only gather data provided before this date (closed interval). '
         'Default is tomorrow (when dates_range is not set)',
)
parser.add_argument(
    "--dates_range",
    help='List of dates to run the spiders in the format dd/mm/yyyy separated by comma (,). '
         'Not supported when provided with start_date or end_date (choose only one option)',
)
parser.add_argument(
    "--states",
    help='List of states (abbreviated) to run the spiders separated by comma (,)',
)
parser.add_argument(
    "--filename_pattern",
    help='Use this to provide a custom file name to store the data. Default: "data/{state}/covid19-{state}-{date}.csv"',
    default="data/{state}/covid19-{state}-{date}.csv",
)
parser.add_argument(
    "--print_results_only",
    help="Use this flag if you don't want to store the results in a csv, this will only print them in the screen.",
    action='store_true',
)
args = parser.parse_args()

if args.available_spiders:
    display_available_spiders()

elif args.dates_range and (args.start_date or args.end_date):
    raise ValueError("NOT SUPPORTED ERROR: dates_range can't be used simultaneously with start_date/end_date.")

elif args.filename_pattern and args.filename_pattern[-4:] != ".csv":
    raise ValueError("BAD PARAMETER: filename_pattern must end with '.csv'.")

else:
    spiders = get_spiders_to_run(args.states)
    date_params = build_date_parameters(args.start_date, args.end_date, args.dates_range)

    process = CrawlerProcess()

    all_reports = {}
    for spider in spiders:
        reports = {}
        all_reports[spider.name] = reports
        process.crawl(spider, reports=reports, **date_params)
    process.start()

    if args.print_results_only:
        display_results(all_reports)
    else:
        save_results_in_csv(all_reports, args.filename_pattern)

