import datetime
import logging
import re
from functools import lru_cache, partial
from uuid import NAMESPACE_URL, uuid5

from rows.utils.date import today

from . import demographics

logger = logging.getLogger(__name__)
BRASILIO_URLID = "https://id.brasil.io/v1/"
REGEXP_DATE = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}")
CITY_BY_CODE = {}
cities = demographics.cities(2020)
for state in cities.keys():
    for city in cities[state].values():
        CITY_BY_CODE[str(city.city_ibge_code)[:-1]] = city
AGE_RANGES = (
    (0, 4),
    (5, 9),
    (10, 14),
    (15, 19),
    (20, 24),
    (25, 29),
    (30, 34),
    (35, 39),
    (40, 44),
    (45, 49),
    (50, 54),
    (55, 59),
    (60, 64),
    (65, 69),
    (70, 74),
    (75, 79),
    (80, 84),
    (85, 89),
    (90, float("inf")),
)


@lru_cache(maxsize=999)
def calculate_age_range(value):
    """
    >>> calculate_age_range('10/2020')
    '00 a 04'
    >>> calculate_age_range('0')
    '00 a 04'
    >>> calculate_age_range('15')
    '15 a 19'
    >>> calculate_age_range('36')
    '35 a 39'
    >>> calculate_age_range('80')
    '80 a 84'
    >>> calculate_age_range('88')
    '85 a 89'
    >>> calculate_age_range('90')
    '90+'
    """

    if isinstance(value, str) and "/" in value:
        # TODO: deveria devolver "00 a 04"?
        return None

    value = parse_int(value)
    if not value:
        return None

    for start, end in AGE_RANGES:
        if start <= value <= end:
            if end == float("inf"):
                return f"{start:02d}+"
            else:
                return f"{start:02d} a {end:02d}"


def generate_uuid(entity):
    url = BRASILIO_URLID + entity + "/"
    def gen(internal_id):
        return str(uuid5(NAMESPACE_URL, url + internal_id))
    return gen


def parse_str(value):
    value = (value or "").replace("\xa0", "").strip()
    return value if value and value not in ('\\\\""', "\\\\") else None

@lru_cache(maxsize=16)
def parse_vacina(value):
    mapping = {
        "Covid-19-AstraZeneca": "covishield",
        "Covid-19-Coronavac-Sinovac/Butantan": "coronavac",
        "Pendente Identificação": None,
        "Vacina Covid-19 - Covishield": "covishield",
        "Vacina covid-19 - Ad26.COV2.S - Janssen-Cilag": "ad26cov2s",
        "Vacina covid-19 - BNT162b2 - BioNTech/Fosun Pharma/Pfizer": "bnt162b2",
    }
    result = mapping.get(value, "***NOT FOUND***")
    if result == "***NOT FOUND***":
        logger.warning(f"Vaccine not found: {repr(value)}")
        return parse_str(value)
    else:
        return result


@lru_cache(maxsize=9)
def parse_str_capitalize(value):
    value = parse_str(value)
    return value.capitalize() if value is not None else None


@lru_cache(maxsize=64)
def parse_sistema_origem(value):
    mapping = {
        "E-saúde Curitiba": "E-Saúde",
        "E-saúde": "E-Saúde",
        "ESUS APS - NACIONAL (OFFLINE)": "e-SUS APS",
        "FAST MEDIC - FAST SAUDE": "FastMedic",
        "Fastmedic - FastSaude": "FastMedic",
        "G-MUS - Gestão Municipal de Saude": "G-MUS",
        "G-MUS - Gestão Municipal de Saúde": "G-MUS",
        "G-MUS": "G-MUS",
        "GMUS": "G-MUS",
        "IDS SAUDE": "IDS Saúde",
        "IDS Saúde": "IDS Saúde",
        "IPM Sistemas Ltda": "IPM Saúde",
        "IPM Sistemas Ltda.": "IPM Saúde",
        "IPM Sistemas": "IPM Saúde",
        "IPM istemas LTDA": "IPM Saúde",
        "IntegraSUS": "IntegraSUS",
        "Novo PNI": "Novo PNI",
        "Prontuário Sobral": "Prontuário Sobral",
        "RN + Vacina": "RN + Vacina",
        "RP SAÚDE": "RP Saúde",
        "RP Saúde": "RP Saúde",
        "SIGRAH": "SIGRAPH",
        "SIGSS - Sistema de Gestão de Saúde Social": "SIGSS",
        "SIGSS MV": "SIGSS MV",
        "SIGSS ¿ Sistema Integrado de Gestão da Saúde e Social": "SIGSS",
        "SIMUS": "SIMUS",
        "SMV": "SMV",
        "Sanitas - Sistema Integrado de Saúde": "Sanitas",
        "Saudetech": "SaúdeTech",
        "Saúde Digital MG": "Saúde Digital MG",
        "Sistema Gestor de Saúde": "SGS",
        "VACINOMENTRO COVID-19": "Vacinômetro COVID-19",
        "VACIVIDA": "VaciVida",
        "VIDA+": "Vida+",
        "Vacina Campo Grande": "Vacina Campo Grande",
        "Vacina João Pessoa": "Vacina João Pessoa",
        "saudetech": "SaúdeTech",
    }
    result = mapping.get(value, "***NOT FOUND***")
    if result == "***NOT FOUND***":
        logger.warning(f"Health system not found: {repr(value)}")
        return parse_str(value)
    else:
        return result


@lru_cache(maxsize=99999)
def parse_codigo_5_digitos(value):
    value = parse_str(value)
    return f"{int(value):05d}" if value is not None else None


@lru_cache(maxsize=99)
def parse_subgrupo(value):
    # Using this as a separate function just for cache (can't cache too many
    # values in parse_str)
    return parse_str(value)


@lru_cache(maxsize=9999)
def parse_int(value):
    if isinstance(value, int):
        return value
    value = parse_str(value)
    return int(value) if value is not None else None


@lru_cache(maxsize=9999)
def parse_codigo_ibge_municipio(value):
    value = parse_int(value)
    return f"{value:06d}" if value not in (999999, None) else None


@lru_cache(maxsize=9999)
def parse_municipio(value):
    value = parse_str(value)
    return value if value != "INVALIDO" else None


@lru_cache(maxsize=99)
def parse_unidade_federativa(value):
    value = parse_str(value)
    return value if value != "XX" else None


@lru_cache(maxsize=9)
def parse_etnia(value):
    return {
        "": None,
        "AMARELA": "Amarela",
        "BRANCA": "Branca",
        "INDIGENA": "Indígena",
        "PARDA": "Parda",
        "PRETA": "Preta",
        "SEM INFORMACAO": None,
    }[value]


@lru_cache(maxsize=9)
def parse_dose(value):
    mapping = {
        "1ª dose": 1,
        "única": 1,
        "2ª dose": 2,
        "dose": None,
    }
    converted = parse_str(value).lower().replace("ªdose", "ª dose")
    if converted not in mapping:
        logger.warning(f"Incorrect dose number: {repr(value)} (converted to `None`)")
    return mapping.get(converted, None)


@lru_cache(maxsize=99999)
def parse_date(value):
    value = (value or "").strip()
    if not value:
        return None

    match = REGEXP_DATE.match(value)
    if match is None:
        raise ValueError(f"Invalid date: {repr(value)}")
    return match.group()


@lru_cache(maxsize=99999)
def calculate_age(start_date, end_date):
    """
    >>> calculate_age('1990-05-01', '2021-01-01')
    30
    >>> calculate_age('1990-05-01', '2021-05-01')
    31
    >>> calculate_age('1990-05-01', '2021-07-01')
    31
    >>> calculate_age('2020-02-29', '2021-02-28')
    0
    >>> calculate_age('2020-02-29', '2021-03-01')
    1

    """
    start_date, end_date = parse_date(start_date), parse_date(end_date)
    if not start_date or not end_date:
        return

    start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    age = end.year - start.year
    if start_date[5:] > end_date[5:]:
        age -= 1

    return str(age)


@lru_cache(maxsize=99999)
def parse_date_str(value):
    return value[:10] if value else None


@lru_cache(maxsize=999)
def parse_application_date(value):
    value = parse_date(value)
    if value is None or value <= "2020-01-01" or value >= str(today()):  # Invalid value
        value = None
    return value


@lru_cache(maxsize=9999)
def clean_municipio(state, name, code):
    # TODO: parse 'JUIZ DE FORA - MG' (city name)
    if state is None or name is None:
        return state, name, code
    elif name.startswith("MUNICIPIO IGNORADO"):
        return state, None, code

    # Fix city names/codes (inconsistent input)
    if state == "CE" and code == "230395":
        name = "CHOROZINHO"
    elif state == "DF":
        name = "Brasília"
    elif state == "RS" and name == "CERRO LARGO":
        code = 4305207
    elif state == "GO" and name.endswith("(TRANSF. P/TO)"):
        logger.warning(
            f"Incorrect city code for: {repr(state)}, {repr(name)}, {repr(code)}. Fixing to state = TO"
        )
        state, name = "TO", name.replace("(TRANSF. P/TO)", "").strip()
    elif state == "SP" and name.upper() in ("PEDRO TOLEDO", "PEDRO DE TOLEDO"):
        code = demographics.get_city(state, name).city_ibge_code

    city_obj = demographics.get_city(state, name) or CITY_BY_CODE.get(code, None)

    if city_obj is None:
        raise ValueError(f"Incorrect city name/state for: {repr(state)}, {repr(name)}, {repr(code)}")
    elif str(city_obj.city_ibge_code)[:-1] != str(code):
        if code not in CITY_BY_CODE:
            logger.warning(
                f"Incorrect city code for: {repr(state)}, {repr(name)}, {repr(code)} (expected: {repr(city_obj.city_ibge_code)})"
            )
        else:
            raise ValueError(
                f"Conflict in city name/code for: {repr(state)}, {repr(name)}, {repr(code)} (the city with this name has another code: {repr(city_obj.city_ibge_code)})"
            )

    return city_obj.state, city_obj.city, f"{city_obj.city_ibge_code:07d}"


def get_field_converters():
    mapping = {
        "@timestamp": {"name": "timestamp", "converter": None,},
        "@version": {"name": "version", "converter": None,},
        "data_importacao_rnds": {"name": "data_importacao", "converter": parse_date_str,},
        "document_id": {"name": "documento_uuid", "converter": generate_uuid("covid19-documento-vacinacao"),},
        "estabelecimento_municipio_codigo": { "name": "estabelecimento_codigo_ibge_municipio", "converter": parse_codigo_ibge_municipio, },
        "estabelecimento_municipio_nome": {"name": "estabelecimento_municipio", "converter": parse_municipio,},
        "estabelecimento_razaoSocial": {"name": "estabelecimento_razao_social", "converter": parse_str,},
        "estabelecimento_uf": {"name": "estabelecimento_unidade_federativa", "converter": parse_unidade_federativa,},
        "estabelecimento_valor": {"name": "estabelecimento_codigo_cnes", "converter": parse_int,},
        "estalecimento_noFantasia": {"name": "estabelecimento", "converter": parse_str,},
        "id_sistema_origem": {"name": "sistema_origem_id", "converter": parse_int,},
        "paciente_dataNascimento": {"name": "paciente_data_nascimento", "converter": parse_date,},
        "paciente_endereco_cep": {"name": "paciente_cep", "converter": parse_codigo_5_digitos,},
        "paciente_endereco_coIbgeMunicipio": { "name": "paciente_codigo_ibge_municipio", "converter": parse_codigo_ibge_municipio, },
        "paciente_endereco_coPais": {"name": "paciente_codigo_pais", "converter": parse_int,},
        "paciente_endereco_nmMunicipio": {"name": "paciente_municipio", "converter": parse_municipio,},
        "paciente_endereco_nmPais": {"name": "paciente_pais", "converter": parse_str_capitalize,},
        "paciente_endereco_uf": {"name": "paciente_unidade_federativa", "converter": parse_unidade_federativa,},
        "paciente_enumSexoBiologico": {"name": "paciente_sexo_biologico", "converter": parse_str,},
        "paciente_id": {"name": "paciente_uuid", "converter": generate_uuid("covid19-documento-vacinado"),},
        "paciente_idade": {"name": "paciente_idade", "converter": None,},
        "paciente_nacionalidade_enumNacionalidade": {"name": "paciente_nacionalidade", "converter": parse_str,},
        "paciente_racaCor_codigo": {"name": "paciente_codigo_etnia", "converter": parse_int,},
        "paciente_racaCor_valor": {"name": "paciente_etnia", "converter": parse_etnia,},
        "sistema_origem": {"name": "sistema_origem", "converter": parse_sistema_origem,},
        "vacina_categoria_codigo": {"name": "paciente_codigo_grupo", "converter": parse_int,},
        "vacina_categoria_nome": {"name": "paciente_grupo", "converter": parse_str,},
        "vacina_codigo": {"name": "codigo_vacina", "converter": parse_int,},
        "vacina_dataAplicacao": {"name": "data_aplicacao", "converter": parse_application_date,},
        "vacina_descricao_dose": {"name": "numero_dose", "converter": parse_dose,},
        "vacina_fabricante_nome": {"name": "fabricante", "converter": parse_str,},
        "vacina_fabricante_referencia": {"name": "codigo_fabricante", "converter": parse_str,},
        "vacina_grupoAtendimento_codigo": {"name": "paciente_codigo_subgrupo", "converter": parse_int,},
        "vacina_grupoAtendimento_nome": {"name": "paciente_subgrupo", "converter": parse_subgrupo,},
        "vacina_lote": {"name": "vacina_lote", "converter": parse_str,},
        "vacina_nome": {"name": "vacina", "converter": parse_vacina,},
    }
    return {key.lower(): value for key, value in mapping.items()}


def censor(row):
    # TODO: verificar se as colunas referentes ao fabricante estão consistentes
    # e, caso estejam, não deletá-las (em 2021-02-12 estavam totalmente
    # inconsistentes, comparadas com vacina e codigo_vacina).

    del row["fabricante"]
    del row["codigo_fabricante"]
    del row["paciente_data_nascimento"]


def convert_row(field_converters):

    def convert(row):
        # First, convert fields already in `row`
        new = {}
        for key, value in row.items():
            field_meta = field_converters[key]
            converter = field_meta["converter"]
            if converter is not None:
                new[field_meta["name"]] = converter(value)

        # Then, add `None` to fields not in `row`
        new.update(
            {
                meta["name"]: None
                for meta in field_converters.values()
                if meta["name"] not in new.keys() and meta["converter"] is not None
            }
        )

        # Run transformation on fields which need other field values
        (
            new["paciente_unidade_federativa"],
            new["paciente_municipio"],
            new["paciente_codigo_ibge_municipio"],
        ) = clean_municipio(
            new["paciente_unidade_federativa"], new["paciente_municipio"], new["paciente_codigo_ibge_municipio"],
        )
        (
            new["estabelecimento_unidade_federativa"],
            new["estabelecimento_municipio"],
            new["estabelecimento_codigo_ibge_municipio"],
        ) = clean_municipio(
            new["estabelecimento_unidade_federativa"],
            new["estabelecimento_municipio"],
            new["estabelecimento_codigo_ibge_municipio"],
        )
        new["paciente_idade"] = calculate_age(
            row.get("paciente_datanascimento", None),
            row.get("vacina_dataaplicacao", None),
        )
        new["paciente_faixa_etaria"] = calculate_age_range(new["paciente_idade"])

        return new

    return convert


convert_row_uncensored = convert_row(get_field_converters())
