import datetime
import re
from rows.fields import slug
from rows.plugins import pdf

from covid19br.common.constants import State
from covid19br.common.data_normalization_utils import NormalizationUtils
from covid19br.common.demographic_utils import DemographicUtils

REGEXP_DAY_MONTH_YEAR = re.compile("([0-9]+) DE (.+) DE ([0-9]{4})$")


def match_object_from_regexp(regexp, objects):
    """Return the matching result for"""
    for obj in objects:
        result = regexp.findall(obj.text)
        if result:
            return result


def is_only_number(value):
    return re.compile("^([0-9.]+)$").findall(value.strip())


def get_in_same_column(objs_list, obj_reference):
    def x_axis_overlap(obj1, obj2):
        x1min, x1max = obj1.x0, obj1.x1
        x2min, x2max = obj2.x0, obj2.x1
        return (
                (x2min >= x1min and x2max <= x1max)
                or (x1min <= x2min <= x1max)
                or (x1min <= x2min <= x1max)
                or (x1min <= x2max <= x1max)
                or (x1min <= x2max <= x1max)
        )
    return [obj for obj in objs_list if x_axis_overlap(obj, obj_reference)]


class RioGrandeDoNorteBulletinExtractor:
    """
    ATTENTION: this extractor does not work for old templates of the pdf (the one with graphics before the tables).
    """
    state = State.RN
    demographics = DemographicUtils()

    def __init__(self, filename):
        self.doc = pdf.PyMuPDFBackend(filename)

        self.date = self._extract_date()
        if self.date and self.date < datetime.date(2021, 6, 7):
            raise RuntimeError("This parser does not work for bulletins before 2021-06-07")

    def _extract_date(self):
        first_objects = list(
            next(self.doc.text_objects(
                starts_after=re.compile("ATUALIZADO EM"),
                ends_before=re.compile("PANORAMA EPIDEMIOLÓGICO")))
        )
        day_month_year = match_object_from_regexp(REGEXP_DAY_MONTH_YEAR, first_objects)
        day, month, year = day_month_year[0]
        day = NormalizationUtils.ensure_integer(day)
        month = NormalizationUtils.month_name_to_number(month)
        year = NormalizationUtils.ensure_integer(year)
        return datetime.date(year, month, day)

    @property
    def official_totals(self):
        first_objects = list(
            next(self.doc.text_objects(
                starts_after=re.compile("PANORAMA EPIDEMIOLÓGICO"),
                ends_before=re.compile("PANORAMA ASSISTENCIAL")))
        )
        ordered_objs = sorted(first_objects, key=lambda obj: obj.x0)
        # The confirmed cases label is the first with "casos" on the left
        confirmed_cases_label = next(obj for obj in ordered_objs if obj.text.lower() == "casos")
        # The confirmed cases label is the first with "óbitos" on the left
        deaths_label = next(obj for obj in ordered_objs if 'obitos' in NormalizationUtils.remove_accentuation(obj.text.lower()))
        # The confirmed cases number is the first in the left bellow the cases label and above the deaths label
        confirmed_cases = next((obj for obj in ordered_objs if is_only_number(obj.text) and obj.y0 > confirmed_cases_label.y0 and obj.y0 < deaths_label.y0), None)
        # The deaths number is the first in the left bellow the deaths label
        deaths = next((obj for obj in ordered_objs if is_only_number(obj.text) and obj.y0 > deaths_label.y0), None)

        if confirmed_cases:
            confirmed_cases = NormalizationUtils.ensure_integer(confirmed_cases.text.strip())
        if deaths:
            deaths = NormalizationUtils.ensure_integer(deaths.text.strip())

        return deaths, confirmed_cases

    @property
    def data(self):
        for line in self._get_table_lines():
            city, confirmed, deaths = line
            city = slug(city).replace("_", " ")
            confirmed = NormalizationUtils.ensure_integer(confirmed)
            deaths = NormalizationUtils.ensure_integer(deaths)
            yield {
                "municipio": city,
                "confirmados": confirmed,
                "mortes": deaths,
            }

    def _get_table_lines(self):
        for page_number in range(2, 7):
            starts_after, ends_before = (
                re.compile(REGEXP_DAY_MONTH_YEAR),
                re.compile("Subcoordenadoria de Vigilância Epidemiológica.+"),
            )
            if page_number == 2:
                starts_after = re.compile("Grande do Norte, 2020.+")
            elif page_number == self._get_last_table_page_number():
                ends_before = re.compile("Fonte:.+")
            selected_objects = self.doc.text_objects(
                starts_after=starts_after,
                ends_before=ends_before,
                page_numbers=(page_number,),
            )
            yield from self._extract_lines_from_objects(next(selected_objects))

    def _extract_lines_from_objects(self, text_objects):
        cities_header = next((obj for obj in text_objects if obj.text.strip() == "MUNICÍPIO DE RESIDÊNCIA"), None)
        absolute_nums_headers = sorted([obj for obj in text_objects if obj.text.strip() == "N"], key=lambda ob: ob.x0)
        _, confirmed_header, deaths_header = absolute_nums_headers

        extractor = pdf.YGroupsAlgorithm(
            objects=text_objects,
            y_threshold=-2,  # Objects inside table will intersect each others
            filtered=True,
        )

        # There is ONE line in the pdf table that has an odd space between the city name and the numbers.
        # When we reach it, we need to merge it's value with the nex line of the extractor
        join_with_previous_line = False
        for raw_line in extractor.get_lines():
            flat_line = [item for sublist in filter(None, raw_line) for item in sublist]

            if join_with_previous_line:
                flat_line.extend(join_with_previous_line)
                join_with_previous_line = False

            city_words = [city.text.strip() for city in get_in_same_column(flat_line, cities_header)]
            confirmed_objs = get_in_same_column(flat_line, confirmed_header)
            deaths_objs = get_in_same_column(flat_line, deaths_header)

            if not city_words or "MUNICÍPIO DE RESIDÊNCIA" in city_words:  # is the header column, we can skip
                continue

            # Here we have the odd case of the line with messed up spaces
            # We just need to join it with the next one to properly have a complete line
            if not confirmed_objs and not deaths_objs:
                join_with_previous_line = flat_line
                continue

            city = " ".join(city_words)
            confirmed = self._separate_grouped_values(confirmed_objs[0])
            if deaths_objs:
                deaths = self._separate_grouped_values(deaths_objs[0])
            else:
                deaths = None
            yield city, confirmed, deaths

    @staticmethod
    def _separate_grouped_values(obj):
        """
        Sometimes the values of two columns are so close in the table that the extractor considers it to be one.
        This method properly handles such case, keeping in mind that the neighbor columns for N are "... descartados"
        on the left that have integer values and "... por 100.000 hab" on the right that has a float value.
        """
        text = obj.text.strip()
        if " " not in text:
            return text

        nums = text.split()
        if "," in nums[-1]:  # the column was merged with the right neighbor
            return nums[-2]
        return nums[1]  # the column was merged with the left neighbor

    def _get_last_table_page_number(self):
        if self.date and self.date < datetime.date(2021, 6, 24):
            return 7
        return 6
