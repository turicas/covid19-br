from collections import Counter
import datetime
import re
from rows.plugins import pdf
from rows.fields import slug

from covid19br.common.data_normalization_utils import RowsPtBrIntegerField, NormalizationUtils

REGEXP_PTBR_DATE = re.compile("^[0-9]+ de [^ ]+ de [0-9]+$")


def find_first_by_texts(objs, possible_texts):
    """Find the first TextObject which matches one of the possible texts"""
    if not isinstance(possible_texts, (tuple, list)):
        raise TypeError("`possible_texts` must be a tuple or list")
    possible_texts = [slug(str(text or "")) for text in possible_texts]
    for obj in objs:
        if slug(str(obj.text or "")) in possible_texts:
            return obj

    return None


class RondoniaBulletinExtractor:
    # Works for PDF files >= 2021-01-18 (bulletin #290)

    def __init__(self, filename, use_ocr=False):
        # Check if the file is really a PDF
        with open(filename, mode="rb") as fobj:
            sample = fobj.read(1024)
            if not sample.startswith(b"%PDF"):
                raise RuntimeError("This file is not a PDF")

        self.filename = filename
        self.doc = pdf.PyMuPDFBackend(filename)
        self.use_ocr = use_ocr
        self._date = -1

    @property
    def date(self):
        if self._date == -1:
            date = None
            objects = next(self.doc.text_objects())
            for obj in objects:
                if REGEXP_PTBR_DATE.match(obj.text.strip()):
                    date = obj.text.strip()
                    break
            self._date = NormalizationUtils.extract_in_full_date(date)
        return self._date

    def _get_pages_text(self):
        for page_objects in self.doc.text_objects(page_numbers=(3, 4)):
            yield page_objects

    def _get_pages_ocr(self):
        def check_group(axis, obj1, obj2, threshold):
            return pdf.check_merge_x(obj1, obj2, threshold)

        doc = pdf.PyMuPDFTesseractBackend(self.filename)
        for page_number, page in enumerate(doc.pages, start=1):
            if page_number in (3,  4):
                # We won't use `merge_x` since there's no way to pass a
                # threshold - then we need to group objects manually.
                # NOTE: using `dpi` values different than 270 (even greater
                # values) will make Tesseract identify some numbers as letters.
                original_objs = doc.page_objects(page, dpi=270, lang="por", merge_x=False)
                line_height = original_objs[0].y1 - original_objs[0].y0
                groups = pdf.group_objects("y", original_objs, threshold=-line_height / 10)
                objs = []
                for group in groups:
                    objs.extend(pdf.group_objects("y", group, check_group=check_group))
                yield objs

    def _get_pages(self):
        if self.use_ocr or self.date == datetime.date(2021, 5, 2):
            # This date has multiple hidden objects, so force using OCR
            yield from self._get_pages_ocr()
        yield from self._get_pages_text()

    def _get_page_objects(self):
        """Get page objects in which the table is (will filter out unneeded ones)

        It's usually the 3rd page, but at least in one case it's on the 4th, so
        use the capital city to identify (it'll be the first to appear on the
        cases/deaths table).
        """
        found = False
        for page_objects in self._get_pages():
            page_text = " ".join(str(obj.text or "").strip() for obj in page_objects if str(obj.text or "").strip())
            if "porto velho" in page_text.lower():
                found = True
                break
        if not found:
            raise RuntimeError("Cannot find the correct page")

        # Filter out unneeded objects so we can identify table boundaries easier
        objs = []
        for obj in page_objects:
            text = str(obj.text or "").strip().lower()
            if (
                not text  # Remove empty ones
                or len(text) > 50  # Skip disclaimers at the bottom of the page
                or text in ("totais", "ativos")
                # Big header font will split this part as another object (from
                # "Casos totais"), so ignore the second line
            ):
                continue
            objs.append(obj)

        return objs

    def _get_table_lines(self, objs):
        # Identify the first and last objects of the table, so we can filter
        # all the desired objects
        groups = pdf.group_objects("y", objs, check_group=pdf.object_contains_center)
        len_counter = Counter(len(group.objects) for group in groups)
        most_common_len, _ = len_counter.most_common(1)[0]
        possible_rows = [group for group in groups if len(group.objects) == most_common_len]
        possible_objs = []
        for group in possible_rows:
            possible_objs.extend(group.objects)
        first_obj = sorted(possible_objs, key=lambda obj: obj.y0)[0]
        last_obj = sorted(possible_objs, key=lambda obj: obj.y1, reverse=True)[0]
        first_y, last_y = first_obj.y0, last_obj.y1
        obj_municipio = find_first_by_texts(objs, ("município", "municipio"))
        obj_total = last_obj = find_first_by_texts(objs, ("total geral", ))

        # Select all the objects on the table
        table_objs = sorted(
            [
                group
                for group in objs
                if group.y0 >= first_y and group.y0 <= last_y
            ],
            key=lambda obj: (obj.y0, obj.x0),
        )
        if obj_municipio is not None and obj_municipio not in table_objs:
            # In this case the other objects are joined together
            obj_municipio = None

        # Get table lines
        lines = [
            [obj.text for obj in line]
            for line in pdf.group_objects("y", table_objs, check_group=pdf.object_contains_center)
        ]

        if obj_municipio is not None:
            header = lines.pop(0)
        else:  # Header not found
            header = ["Município", "Casos Totais", "Óbitos Totais", "Curados Totais", "Casos Ativos", "Letalidade"]

        yield header
        yield from lines

    @property
    def data(self):
        if self.date is not None and self.date < datetime.date(2021, 1, 18):
            raise RuntimeError("This parser does not work for bulletins before 2021-01-18")
        objs = self._get_page_objects()
        lines = self._get_table_lines(objs)
        header = next(lines)
        for line in lines:
            row = {slug(key): value for key, value in zip(header, line)}
            for key in ("casos_totais", "obitos_totais"):
                if key not in row:
                    key = key.replace("_totais", "")
                row[key] = RowsPtBrIntegerField.deserialize(row[key])
            municipio = row["municipio"].strip()
            yield {
                "municipio": municipio if not municipio.lower().startswith("total") else "TOTAL NO ESTADO",
                "confirmados": row.get("casos_totais", row.get("casos")),
                "mortes": row.get("obitos_totais", row.get("obitos")),
            }


if __name__ == "__main__":
    import argparse

    import rows

    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr", action="store_true")
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    parser = RondoniaBulletinExtractor(args.input_filename, use_ocr=args.ocr)
    date = parser.date
    print(f"Extracting table for date {date}...")

    writer = rows.utils.CsvLazyDictWriter(args.output_filename)
    for row in parser.data:
        writer.writerow(row)
    writer.close()
