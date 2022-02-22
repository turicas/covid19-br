from collections import namedtuple
from enum import Enum

BulletinWarning = namedtuple("BulletinWarning", "slug description")


class WarningType(Enum):
    SOURCES_DONT_MATCH = "fontes-diferem-casos-municipios"
    TOTAL_DONT_MATCH = "verificar-total"
    MISSING_COUNTY_BULLETINS = "faltando-boletins-por-estado"
    MISSING_IMPORTED_UNDEFINED_CASES = "faltando-casos-importados-ou-indefinidos"
    MISSING_CONFIRMED_CASES = "faltando-casos-confirmados"
    MISSING_DEATHS = "faltando-obitos"
    NO_OFFICIAL_TOTAL = "total-oficial-nao-considerado"
    ONLY_TOTAL = "apenas-total"
