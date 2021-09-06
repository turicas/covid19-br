import argparse
import csv
from pathlib import Path

import ckanapi
import rows
from tqdm import tqdm

from covid19br.vacinacao import calculate_age_range


CKAN_URL = "https://opendatasus.saude.gov.br/"
SRAG_DATASETS = (
    "bd-srag-2021",  # Primeiro porque possui mais colunas
    "bd-srag-2020",
)
DOWNLOAD_PATH = Path(__file__).parent / "data" / "download"
OUTPUT_PATH = Path(__file__).parent / "data" / "output"
for path in (DOWNLOAD_PATH, OUTPUT_PATH):
    if not path.exists():
        path.mkdir(parents=True)


class PtBrDateField(rows.fields.DateField):
    INPUT_FORMAT = "%d/%m/%Y"

    @classmethod
    def deserialize(cls, value):
        if not (value or "").strip():
            return None
        elif value.count("/") == 2 and len(value.split("/")[-1]) == 2:
            parts = value.split("/")
            value = f"{parts[0]}/{parts[1]}/20{parts[2]}"
        return super().deserialize(value)


def get_csv_resources(dataset_name):
    api = ckanapi.RemoteCKAN(CKAN_URL)

    dataset = api.call_action("package_show", {"id": dataset_name})
    for resource in dataset["resources"]:
        if resource["format"] == "CSV":
            yield resource["url"]


def download_files():
    for dataset in SRAG_DATASETS:
        csv_url = next(get_csv_resources(dataset))
        filename = DOWNLOAD_PATH / (Path(csv_url).name + ".gz")
        rows.utils.download_file(
            csv_url,
            filename=filename,
            progress_pattern="Downloading {filename.name}",
            progress=True,
        )
        yield filename


def convert_row(row):
    new = {}
    for key, value in row.items():
        key, value = key.lower(), value.strip()
        if len(value[value.rfind("/") + 1 :]) == 3:
            # TODO: e se for 2021?
            value = value[: value.rfind("/")] + "/2020"
        if not value:
            value = None
        elif key.startswith("dt_") or key in ("dose_1_cov", "dose_2_cov"):
            value = PtBrDateField.deserialize(value)
        new[key] = value

    # TODO: refatorar código que calcula diferença em dias

    diff_days = None
    if new["evolucao"] == "2" and None not in (new["dt_evoluca"], new["dt_interna"]):
        diff_days = (new["dt_evoluca"] - new["dt_interna"]).days
    new["dias_internacao_a_obito_srag"] = diff_days

    diff_days = None
    if new["evolucao"] == "3" and None not in (new["dt_evoluca"], new["dt_interna"]):
        diff_days = (new["dt_evoluca"] - new["dt_interna"]).days
    new["dias_internacao_a_obito_outras"] = diff_days

    diff_days = None
    if new["evolucao"] == "1" and None not in (new["dt_evoluca"], new["dt_interna"]):
        diff_days = (new["dt_evoluca"] - new["dt_interna"]).days
    new["dias_internacao_a_alta"] = diff_days

    diff_days = None
    if new["classi_fin"] == "5" and None not in (new.get("dose_2_cov"), new["dt_sin_pri"]):
        diff_days = (new["dt_sin_pri"] - new["dose_2_cov"]).days
    new["dias_primeiros_sintomas_a_2a_dose"] = diff_days

    new["faixa_etaria"] = calculate_age_range(new["nu_idade_n"])

    # TODO: adicionar coluna ano e semana epidemiológica
    # TODO: corrigir ERROR: cod_idade: invalid input syntax for integer: "20-1"
    # TODO: data nascimento (censurar?)
    # TODO: dt_interna: corrigir valores de anos inexistentes

    return new


def main():
    filenames = download_files()
    output_filename = OUTPUT_PATH / "internacao_srag.csv.gz"
    writer = rows.utils.CsvLazyDictWriter(output_filename)
    for filename in filenames:
        with rows.utils.open_compressed(filename, encoding="utf-8") as fobj:
            reader = csv.DictReader(fobj, delimiter=";")
            for row in tqdm(reader, desc=f"Converting {filename.name}"):
                writer.writerow(convert_row(row))


if __name__ == "__main__":
    main()
