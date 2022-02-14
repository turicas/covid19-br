import datetime
import re
from collections import defaultdict
from rows.fields import slug
from rows.plugins import pdf

from covid19br.common.data_normalization_utils import NormalizationUtils

REGEXP_DAY_MONTH = re.compile("([0-9]+) de (.+)$")
REGEXP_YEAR = re.compile("^de ([0-9]{4})$")


def match_object_from_regexp(regexp, objects):
    """Return the matching result for"""
    for obj in objects:
        result = regexp.findall(obj.text)
        if result:
            return result


def parse_int(value):
    return int(value.replace(".", ""))


class TocantinsBulletinExtractor:
    def __init__(self, filename):
        self.doc = pdf.PyMuPDFBackend(filename)

    @property
    def date(self):
        first_objects = list(
            next(self.doc.text_objects(ends_before=re.compile("^Nº [0-9]+$")))
        )

        day_month = match_object_from_regexp(REGEXP_DAY_MONTH, first_objects)
        day, month = day_month[0]
        day = int(day)
        month = NormalizationUtils.month_name_to_number(month)
        year = match_object_from_regexp(REGEXP_YEAR, first_objects)
        year = int(year[0])

        return datetime.date(year, month, day)

    def _extract_lines_from_objects(self, text_objects):
        """Split tables (if more than one in same page) and yields each line

        Also, remove the hidden objects (numeric values like '828', '295', '71')
        from the city column.
        """

        city_labels = [obj for obj in text_objects if obj.text == "MUNICÍPIO"]
        if not city_labels:  # there's no table on this page
            return

        # Get the last column of first table (table on the left side of the page)
        # and split objects in table1 and table2 based on last columns' x1
        city_label = city_labels[0]
        last_col_labels = sorted(
            [
                obj
                for obj in text_objects
                if (
                    obj.text in ("TOTAL", "ÓBITOS")
                    and pdf.object_intercepts("y", obj, city_label)
                )
            ],
            key=lambda obj: obj.x0,
        )
        objects_table1 = [
            obj for obj in text_objects if obj.x0 <= last_col_labels[0].x1
        ]
        objects_table2 = [obj for obj in text_objects if obj.x0 > last_col_labels[0].x1]

        for table_objects in (objects_table1, objects_table2):
            if not table_objects:
                continue

            # Remove hidden numbers in "MUNICÍPIO" column (they'd mess with the
            # Y-Groups algorithm)
            second_col_label = sorted(
                [obj for obj in table_objects if obj.text in ("TOTAL", "CASOS")],
                key=lambda obj: (obj.y0, obj.x0),
            )[0]
            table_objects = [
                obj
                for obj in table_objects
                if obj.x1 >= second_col_label.x0
                or (obj.x1 < second_col_label.x0 and not obj.text.isdigit())
            ]
            extractor = pdf.YGroupsAlgorithm(
                objects=table_objects,
                y_threshold=-2,  # Objects inside table will intersect each others
                filtered=True,
            )
            for raw_line in extractor.get_lines():
                line = [self.doc.get_cell_text(cell) for cell in raw_line]
                if line in (
                    ["MUNICÍPIO", "TOTAL"],
                    ["MUNICÍPIO\nMUNICÍPIO", "TOTAL\nTOTAL"],
                    ["MUNICÍPIO", "CASOS", "ÓBITOS"],
                ):
                    continue
                yield line

    def _identify_layout(self):
        layout, start_page = None, None
        for page_number, page in enumerate(self.doc.text_objects(), start=1):
            for obj in page:
                if obj.text.startswith("TABELA 2"):
                    start_page = page_number
                    if "casos e óbitos confirmados acumulados" in obj.text:
                        layout = "same table"
                    else:
                        layout = "separate tables"
                    break
            if layout is not None:
                break
        if layout is None:
            raise ValueError("Cannot identify layout")
        return layout, start_page

    def _get_table_lines(self, page_number):
        starts_after, ends_before = (
            "município de residência, TOCANTINS.",
            "governodotocantins",
        )
        selected_objects = self.doc.text_objects(
            starts_after=starts_after,
            ends_before=ends_before,
            page_numbers=(page_number,),
        )
        yield from self._extract_lines_from_objects(next(selected_objects))

    @property
    def data(self):
        layout, start_page = self._identify_layout()

        if layout == "same table":
            for line in self._get_table_lines(start_page):
                city, confirmed, deaths = line
                yield {
                    "city": slug(city).replace("_", " "),
                    "confirmed": parse_int(confirmed),
                    "deaths": parse_int(deaths),
                }

        elif layout == "separate tables":
            result = defaultdict(dict)

            # First, get the cases table
            for line in self._get_table_lines(start_page):
                city, confirmed = line
                result[slug(city)]["confirmed"] = parse_int(confirmed)

            # Second, get the deaths table
            for line in self._get_table_lines(start_page + 1):
                city, deaths = line
                result[slug(city)]["deaths"] = parse_int(deaths)

            for city, city_data in result.items():
                yield {
                    "city": city.replace("_", " "),
                    "confirmed": city_data.get("confirmed"),
                    "deaths": city_data.get("deaths", 0),
                }


if __name__ == "__main__":
    import argparse

    import rows

    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_filename")
    parser.add_argument("csv_filename")
    args = parser.parse_args()

    extractor = TocantinsBulletinExtractor(args.pdf_filename)
    print(f"Extracting data for {extractor.date}")

    writer = rows.utils.CsvLazyDictWriter(args.csv_filename)
    for row in extractor.data:
        writer.writerow(row)
    writer.close()
