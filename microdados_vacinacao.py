import argparse
import csv
import re
from functools import partial, lru_cache
from uuid import uuid5, NAMESPACE_URL

import rows
from rows.utils.date import today
from tqdm import tqdm

from covid19br import demographics


BRASILIO_URLID_PATTERN = "https://id.brasil.io/v1/{entity}/{internal_id}"
REGEXP_DATE = re.compile("[0-9]{4}-[0-9]{2}-[0-9]{2}")
CITY_BY_CODE = {}
cities = demographics.cities(2020)
for state in cities.keys():
    for city in cities[state].values():
        CITY_BY_CODE[str(city.city_ibge_code)[:-1]] = city


def generate_uuid(entity, internal_id):
    return uuid5(NAMESPACE_URL, BRASILIO_URLID_PATTERN.format(entity=entity, internal_id=internal_id))


def parse_str(value):
    value = value.replace("\xa0", "").strip()
    return value if value and value not in ('\\\\""', "\\\\") else None


@lru_cache(maxsize=9)
def parse_str_capitalize(value):
    value = parse_str(value)
    return value.capitalize() if value is not None else None


@lru_cache(maxsize=9)
def parse_sistema_origem(value):
    value = parse_str(value)
    if (
        value
        == "O sistema RN+Vacina auxilia o Governo do Estado em todo o processo logístico da cadeia de frio do Rio Grande do Norte e da aplicação de vacinas nos usuários do Sistema ínico de Saúde, permitindo o controle e transparência de ponta-a-ponta."
    ):
        value = "RN+Vacina"
    return value


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
    return {"1ª dose": 1, "2ª dose": 2}[parse_str(value).lower().replace("ªdose", "ª dose")]


@lru_cache(maxsize=99999)
def parse_date(value):
    value = value.strip()
    if not value:
        return None

    match = REGEXP_DATE.match(value)
    if match is None:
        raise ValueError(f"Invalid date: {repr(value)}")
    return match.group()

@lru_cache(maxsize=999)
def parse_application_date(value):
    value = parse_date(value)
    if value <= '2020-01-01' or value >= str(today()):  # Invalid value
        value = None
    return value

@lru_cache(maxsize=9999)
def clean_municipio(state, name, code):
    if state is None or name is None:
        return state, name, code
    elif name.startswith("MUNICIPIO IGNORADO"):
        return state, None, code

    city_obj = demographics.get_city(state, city) or CITY_BY_CODE.get(code, None)

    if city_obj is None:
        if state == "DF":
            city_obj = demographics.get_city("DF", "Brasília")
        else:
            raise ValueError(f"Incorrect city name/state for: {state}, {name}, {code}")
    elif str(city_obj.city_ibge_code)[:-1] != str(code):
        raise ValueError(f"Incorrect city code for: {state}, {name}, {code} (expected: {city_obj.city_ibge_code})")

    return city_obj.state, city_obj.city, f"{city_obj.city_ibge_code:07d}"


def get_field_converters():
    return {
        "document_id": {"name": "documento_uuid", "converter": partial(generate_uuid, "covid19-documento-vacinacao"),},
        "estabelecimento_municipio_codigo": {
            "name": "estabelecimento_codigo_ibge_municipio",
            "converter": parse_codigo_ibge_municipio,
        },
        "estabelecimento_municipio_nome": {"name": "estabelecimento_municipio", "converter": parse_municipio,},
        "estabelecimento_razaoSocial": {"name": "estabelecimento_razao_social", "converter": parse_str,},
        "estabelecimento_uf": {"name": "estabelecimento_unidade_federativa", "converter": parse_unidade_federativa,},
        "estabelecimento_valor": {"name": "estabelecimento_codigo_cnes", "converter": parse_int,},
        "estalecimento_noFantasia": {"name": "estabelecimento", "converter": parse_str,},
        "paciente_dataNascimento": {"name": "paciente_data_nascimento", "converter": parse_date,},
        "paciente_endereco_cep": {"name": "paciente_cep", "converter": parse_codigo_5_digitos,},
        "paciente_endereco_coIbgeMunicipio": {
            "name": "paciente_codigo_ibge_municipio",
            "converter": parse_codigo_ibge_municipio,
        },
        "paciente_endereco_coPais": {"name": "paciente_codigo_pais", "converter": parse_int,},
        "paciente_endereco_nmMunicipio": {"name": "paciente_municipio", "converter": parse_municipio,},
        "paciente_endereco_nmPais": {"name": "paciente_pais", "converter": parse_str_capitalize,},
        "paciente_endereco_uf": {"name": "paciente_unidade_federativa", "converter": parse_unidade_federativa,},
        "paciente_enumSexoBiologico": {"name": "paciente_sexo_biologico", "converter": parse_str,},
        "paciente_id": {"name": "paciente_uuid", "converter": partial(generate_uuid, "covid19-documento-vacinado"),},
        "paciente_idade": {"name": "paciente_idade", "converter": parse_int,},
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
        "vacina_nome": {"name": "vacina", "converter": parse_str,},
    }

def get_censored_field_converters():
    converters = get_field_converters()

    # TODO: verificar se as colunas referentes ao fabricante estão consistentes
    # e, caso estejam, não deletá-las (em 2021-02-12 estavam totalmente
    # inconsistentes, comparadas com vacina e codigo_vacina).
    converters["vacina_fabricante_nome"]["converter"] = None
    converters["vacina_fabricante_referencia"]["converter"] = None

    converters["paciente_dataNascimento"]["converter"] = None

    return converters


def convert_row(field_converters, row):
    new = {}
    for key, value in row.items():
        field_meta = field_converters[key]
        new_key, converter = field_meta["name"], field_meta["converter"]
        if converter is None:
            continue
        new[new_key] = converter(value)

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

    return new


def convert_file(input_filename, output_filename, progress=True, censor=False):
    writer = rows.utils.CsvLazyDictWriter(output_filename)
    if censor:
        convert_row_func = partial(convert_row, get_censored_field_converters())
    else:
        convert_row_func = partial(convert_row, get_field_converters())
    with rows.utils.open_compressed(input_filename) as in_fobj:
        reader = csv.DictReader(in_fobj)
        if progress:
            reader = tqdm(reader)
        for row in reader:
            writer.writerow(convert_row_func(row))
        writer.close()


if __name__ == "__main__":
    # TODO: mudar entrada de dados para ES
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    parser.add_argument("--no-censorship", action="store_true")
    args = parser.parse_args()

    censor = not args.no_censorship
    convert_file(args.input_filename, args.output_filename, progress=True, censor=censor)
