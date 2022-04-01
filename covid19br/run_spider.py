import argparse
import sys
from datetime import datetime
from pathlib import Path

import rows
from scrapy.crawler import CrawlerProcess

sys.path[0] = "/".join(sys.path[0].split("/")[:-1])

from covid19br.common.data_normalization_utils import NormalizationUtils
from covid19br.spiders.spider_ba import SpiderBA
from covid19br.spiders.spider_ce import SpiderCE
from covid19br.spiders.spider_pr import SpiderPR
from covid19br.spiders.spider_rj import SpiderRJ
from covid19br.spiders.spider_ro import SpiderRO
from covid19br.spiders.spider_sp import SpiderSP
from covid19br.spiders.spider_to import SpiderTO

# Todo -> Automatically retrieve spiders that extend the Base Class
AVAILABLE_SPIDERS = [
    SpiderBA,
    SpiderCE,
    SpiderPR,
    SpiderRO,
    SpiderSP,
    SpiderTO,
    SpiderRJ
]


def save_csv(file_name, csv_rows):
    writer = rows.utils.CsvLazyDictWriter(file_name)
    for row in csv_rows:
        writer.writerow(row)
    writer.close()


def display_available_spiders():
    print("Available spiders:")
    for spider in AVAILABLE_SPIDERS:
        print(f"- {spider.name}")


def get_spiders_to_run(filter_states) -> list:
    if not filter_states:
        return AVAILABLE_SPIDERS
    return [spider for spider in AVAILABLE_SPIDERS if spider.name in filter_states]


def build_date_parameters(start_date=None, end_date=None, dates_list=None) -> dict:
    if dates_list:
        return {
            "dates_list": [
                NormalizationUtils.str_to_date(date_) for date_ in dates_list.split(",")
            ]
        }
    params = {}
    if start_date:
        params["start_date"] = NormalizationUtils.str_to_date(start_date)
    if end_date:
        params["end_date"] = NormalizationUtils.str_to_date(end_date)
    if start_date and end_date and params["start_date"] > params["end_date"]:
        raise ValueError("BAD PARAMETER: end_date should be greater than start_date.")
    return params


def display_results(results):
    print("\n" "\n---------" "\nREPORTS" "\n---------")
    for state, reports_by_date in results.items():
        print(f"{state}:")
        if not reports_by_date:
            print("- No report found")
            continue
        for date in sorted(reports_by_date):
            report = reports_by_date[date]
            print(f"- ({report.reference_date}) {report}")


def save_results_in_csv(results, filename_pattern):
    print("\n" "\n---------------" "\nSAVING REPORTS" "\n---------------")
    for state, reports_by_date in results.items():
        if not reports_by_date:
            print(f"No report found for {state} - skipping...")
            continue
        for date, report in sorted(reports_by_date.items()):
            filename = Path(
                filename_pattern.format(
                    date=report.reference_date,
                    state=report.state.value,
                    extra_info=report.warnings_slug,
                )
            )
            if not filename.parent.exists():
                filename.parent.mkdir(parents=True)
            print(f"({report.reference_date}) Formatting and saving file {filename}...")
            save_csv(filename, report.to_csv_rows())


def save_metadata(results):
    print("\n" "\n---------------" "\nSAVING METADATA" "\n---------------")
    extraction_time = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    base_path = "data/metadata"
    csv_filename = Path(f"{base_path}/covid-19-metadata__{extraction_time}.csv")
    txt_filename = Path(f"{base_path}/covid-19-metadata__{extraction_time}.txt")
    if not csv_filename.parent.exists():
        csv_filename.parent.mkdir(parents=True)

    bulletins = sorted(
        [
            report
            for reports_by_date in results.values()
            if reports_by_date
            for report in reports_by_date.values()
        ],
        key=lambda x: x.state.value,
    )
    csv_rows = [bulletin.export_metadata_in_csv() for bulletin in bulletins]
    txt_lines = [bulletin.export_metadata_in_text() for bulletin in bulletins]

    print(f"Formatting and saving metadata file {csv_filename}...")
    save_csv(csv_filename, csv_rows)
    print(f"Formatting and saving metadata file {txt_filename}...")
    with open(txt_filename, "w") as f:
        f.write("\n\n".join(txt_lines))


parser = argparse.ArgumentParser(
    description="Runs spiders to get covid-19 data for one or more states in specified dates."
)
parser.add_argument(
    "--available-spiders",
    help="list the names of all available spiders",
    action="store_true",
)
parser.add_argument(
    "--start-date",
    help="Date in the format dd/mm/yyyy. "
    "The spiders only gather data provided after this date (open interval). "
    "Default is today (when dates-list is not set)",
)
parser.add_argument(
    "--end-date",
    help="Date in the format dd/mm/yyyy. "
    "The spiders only gather data provided before this date (closed interval). "
    "Default is tomorrow (when dates-list is not set)",
)
parser.add_argument(
    "--dates-list",
    help="List of dates to run the spiders in the format dd/mm/yyyy separated by comma (,). "
    "Not supported when provided with start_date or end_date (choose only one option)",
)
parser.add_argument(
    "--states",
    help="List of states (abbreviated) to run the spiders separated by comma (,)",
)
parser.add_argument(
    "--filename-pattern",
    help='Use this to provide a custom file name to store the data. Default: "data/{state}/covid19-{state}-{date}.csv"',
    default="data/{state}/covid19-{state}-{date}{extra_info}.csv",
)
parser.add_argument(
    "--print-results-only",
    help="Use this flag if you don't want to store the results in a csv, this will only print them in the screen.",
    action="store_true",
)
parser.add_argument(
    "--also-export-metadata",
    help="Use this flag if you want to save a csv with metadata from the scrapped data (such as sources, warnings, "
    "etc.). The result is saved in the folder data/metadata in the files covid-19-metadata__{extraction_time}.csv"
    "and covid-19-metadata__{extraction_time}.txt",
    action="store_true",
)
args = parser.parse_args()

if args.available_spiders:
    display_available_spiders()

elif args.dates_list and (args.start_date or args.end_date):
    raise ValueError(
        "NOT SUPPORTED ERROR: dates_list can't be used simultaneously with start_date/end_date."
    )

elif args.filename_pattern and args.filename_pattern[-4:] != ".csv":
    raise ValueError("BAD PARAMETER: filename_pattern must end with '.csv'.")

else:
    spiders = get_spiders_to_run(args.states)
    if not spiders:
        raise ValueError(f"BAD PARAMETER: No state '{args.states}' found")

    date_params = build_date_parameters(args.start_date, args.end_date, args.dates_list)

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

    if args.also_export_metadata:
        save_metadata(all_reports)
