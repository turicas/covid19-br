import re
import rows

from covid19br.common.data_normalization_utils import NormalizationUtils


def is_only_number(value):
    return re.compile("^([0-9.]+)$").findall(value.strip())


class MaranhaoPdfBulletinExtractor:
    def __init__(self, filename):
        self.doc = rows.plugins.pdf.PyMuPDFBackend(filename)
        self.first_page_objs = next(self.doc.text_objects())

    @property
    def date(self):
        for obj in self.first_page_objs:
            if "BOLETIM ATUALIZADO" in obj.text:
                return NormalizationUtils.extract_numeric_date(obj.text)

    @property
    def official_total(self):
        confirmed_cases_label = next(
            obj for obj in self.first_page_objs if obj.text.lower() == "confirmados"
        )
        deaths_label = next(
            obj for obj in self.first_page_objs if obj.text.lower() == "óbitos"
        )

        # select the number above and on the left of confirmed_cases_label
        confirmed_cases = next(
            obj
            for obj in self.first_page_objs
            if is_only_number(obj.text)
            and obj.y0 < confirmed_cases_label.y0
            and obj.x0 < confirmed_cases_label.x0
        )
        # select the numbers above and that are in the same column as deaths_label and pick the closest one
        deaths, *_ = sorted(
            [
                obj
                for obj in self.first_page_objs
                if is_only_number(obj.text)
                and obj.y0 < deaths_label.y0
                and obj.x0 < deaths_label.x0
                and obj.x1 > deaths_label.x1
            ],
            key=lambda obj: deaths_label.y0 - obj.y0,
        ) or [None]

        return {"confirmados": deaths.text, "mortes": confirmed_cases.text}
