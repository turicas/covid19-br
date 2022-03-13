import re
from rows.plugins import pdf

from covid19br.common.constants import State
from covid19br.common.data_normalization_utils import NormalizationUtils
from covid19br.parsers.extractor_utils import match_object_from_regexp, is_only_number

REGEXP_DATE = re.compile("([0-9]+) de (.+) de ([0-9]{4})$")
CITY_NAME_TABLE_COLUMN = 0
CONFIRMED_CASES_TABLE_COLUMN = 2
DEATH_CASES_TABLE_COLUMN = 4


def parse_int(value):
    return int(value.replace(".", ""))


class AcreBulletinExtractor:
    state = State.AC

    def __init__(self, filename):
        self.doc = pdf.PyMuPDFBackend(filename)

    @property
    def date(self):
        first_page_objects = next(
            self.doc.text_objects(
                starts_after=re.compile("BOLETIM(.+)"),
                ends_before=re.compile("SITUAÇÃO ATUAL(.+)"),
            )
        )
        date_obj, *_ = match_object_from_regexp(REGEXP_DATE, first_page_objects) or [
            None
        ]
        if date_obj:
            return NormalizationUtils.extract_in_full_date(" ".join(date_obj))

    @property
    def official_total(self):
        first_page_objects = next(
            self.doc.text_objects(
                starts_after=re.compile("SITUAÇÃO ATUAL(.+)"),
                ends_before=re.compile("DISTRIBUIÇÃO DOS CASOS(.+)"),
            )
        )

        # Unfortunately the text labels are images which makes difficult for us to get the numbers based on them
        # So we are going to infer which values we need based on it's position (sometimes there are "ghost objects"
        # in the page, but they are on the far left and won't interfere in this logic.
        remaining_number_objs = [
            obj for obj in first_page_objects if is_only_number(obj.text)
        ]
        # we will start ordering the objects and drop the 2 last of the right (the little numbers on the bulletin)
        ordered_by_x_axis = sorted(remaining_number_objs, key=lambda obj: obj.x0)
        remaining_number_objs = ordered_by_x_axis[:-2]
        # From the 3 numbers on the far right, the death cases is the one most at the bottom
        *_, death_cases_obj = sorted(
            remaining_number_objs[-3:], key=lambda obj: (obj.y0, obj.x0)
        )
        remaining_number_objs = remaining_number_objs[:-3]
        # From the 3 numbers on the right remaining (the middle column), the confirmed cases is the one in the middle
        _, confirmed_cases_obj, _ = sorted(
            remaining_number_objs[-3:], key=lambda obj: (obj.y0, obj.x0)
        )

        return {"confirmados": confirmed_cases_obj.text, "mortes": death_cases_obj.text}

    @property
    def data(self):
        table_page_number = self._get_table_page_number()
        if not table_page_number:
            return None
        page_objs = next(self.doc.text_objects(
            starts_after=re.compile(".+DISTRIBUIÇÃO DOS CASOS CONFIRMADOS.+"),
            ends_before=re.compile("Fonte:.+"),
            page_numbers=(table_page_number,),
        ))

        # remove headers
        city_column_header = next(obj for obj in page_objs if "munic" in obj.text.lower())
        table_objs = [obj for obj in page_objs if obj.y0 > city_column_header.y1]

        lines = pdf.group_objects("y", table_objs, check_group=pdf.object_contains_center)
        for line in lines:
            city = line[CITY_NAME_TABLE_COLUMN].text.strip()
            deaths = line[DEATH_CASES_TABLE_COLUMN].text.strip()
            confirmed = line[CONFIRMED_CASES_TABLE_COLUMN].text.strip()
            yield {
                "municipio": city,
                "confirmados": confirmed,
                "mortes": deaths,
            }

    def _get_table_page_number(self):
        for page_number, page_objs in enumerate(self.doc.text_objects(), start=1):
            for obj in page_objs:
                if "TABELA" in obj.text and "DISTRIBUIÇÃO DOS CASOS CONFIRMADOS" in obj.text:
                    return page_number
