from enum import Enum

NOT_INFORMED_CODE = -1


class PlaceType(Enum):
    CITY = "city"
    STATE = "state"


class State(Enum):
    AC = "AC"
    AL = "AL"
    AP = "AP"
    AM = "AM"
    BA = "BA"
    CE = "CE"
    DF = "DF"
    ES = "ES"
    GO = "GO"
    MA = "MA"
    MT = "MT"
    MS = "MS"
    MG = "MG"
    PA = "PA"
    PB = "PB"
    PR = "PR"
    PE = "PE"
    PI = "PI"
    RJ = "RJ"
    RN = "RN"
    RS = "RS"
    RO = "RO"
    RR = "RR"
    SC = "SC"
    SP = "SP"
    SE = "SE"
    TO = "TO"


class ReportQuality(Enum):
    COUNTY_BULLETINS = "boletins-por-estado"
    UNDEFINED_OR_IMPORTED_CASES = "casos-importados-ou-indefinidos"
    ONLY_TOTAL = "apenas-total"
