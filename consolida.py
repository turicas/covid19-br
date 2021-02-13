import io
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from signal import SIGINT

import rows
import scrapy
from scrapy.exceptions import CloseSpider

from covid19br import converters
from covid19br import demographics

DATA_PATH = Path(__file__).absolute().parent / "data"
ERROR_PATH = DATA_PATH / "error"


class ConsolidaSpider(scrapy.Spider):
    name = "consolida"
    base_url = "https://brasil.io/covid19/import-data/{uf}/"
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
    }

    def __init__(self, boletim_filename, caso_filename, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.boletim_writer = rows.utils.CsvLazyDictWriter(boletim_filename)
        self.caso_filename = caso_filename
        self.caso_writer = rows.utils.CsvLazyDictWriter(self.caso_filename)
        self.errors = defaultdict(list)

    def start_requests(self):
        for state in demographics.states():
            yield scrapy.Request(
                self.base_url.format(uf=state),
                meta={
                    "state": state,
                    "handle_httpstatus_all": True,
                    "caso_filename": self.caso_filename.replace(".csv", f"-state-{state}.csv"),
                },
                callback=self.parse_state_file,
            )

    def parse_boletim(self, state, data):
        self.logger.info(f"Parsing {state} boletim")

        try:
            reports = converters.extract_boletim(state, data)
        except Exception as exp:
            self.errors[state].append(("boletim", state, f"{exp.__class__.__name__}: {exp}"))
            return
        for report in reports:
            self.logger.debug(report)
            self.boletim_writer.writerow(report)

    def parse_caso(self, state, filename, data):
        self.logger.info(f"Parsing {state} caso")

        writer = rows.utils.CsvLazyDictWriter(filename)
        try:
            cases = converters.extract_caso(state, data)
            for row in cases:
                self.logger.debug(row)
                writer.writerow(row)  # state CSV, used in full.py
                self.caso_writer.writerow(row)  # final CSV, used to import data
        except Exception as exp:
            message = f"ERROR PARSING caso for {state}: {exp.args}"
            self.errors[state].append(("caso", state, message))
            self.logger.error(message)
            writer.close()
            return
        writer.close()

    def parse_state_file(self, response):
        meta = response.meta
        state = meta["state"]
        caso_filename = meta["caso_filename"]
        if response.status >= 400:
            self.errors[state].append(("connection", state, f"HTTP status code: {response.status}"))
        else:
            response_data = json.load(io.BytesIO(response.body))
            try:
                self.parse_boletim(state, response_data["reports"])
            except Exception as exp:
                self.errors[state].append(("boletim", state, f"{exp.__class__.__name__}: {exp}"))
            try:
                self.parse_caso(state, caso_filename, response_data["cases"])
            except Exception as exp:
                self.errors[state].append(("caso", state, f"{exp.__class__.__name__}: {exp}"))

        if self.errors[state]:
            error_counter = Counter(error[0] for error in self.errors[state])
            error_counter_str = ", ".join(f"{error_type}: {count}" for error_type, count in error_counter.items())
            self.logger.error(f"{len(self.errors[state])} errors found when parsing {state} ({error_counter_str})")
            error_header = ("sheet", "state", "message")
            errors = rows.import_from_dicts([dict(zip(error_header, row)) for row in self.errors[state]])
            filename = ERROR_PATH / f"errors-{state}.csv"
            if not filename.parent.exists():
                filename.parent.mkdir(parents=True)
            rows.export_to_csv(errors, filename)

    def __del__(self):
        self.boletim_writer.close()
        self.caso_writer.close()

        state_errors = [errors for errors in self.errors.values() if errors]
        if state_errors:
            # Force crawler to stop
            os.kill(os.getpid(), SIGINT)
            os.kill(os.getpid(), SIGINT)
            raise CloseSpider(f"Error found on {len(state_errors)} state(s).")
