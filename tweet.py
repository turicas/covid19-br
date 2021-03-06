import datetime
import hashlib
import json
import os
from decimal import Decimal
from string import Template

import gspread
import rows
from oauth2client.service_account import ServiceAccountCredentials
from rows.utils import open_compressed
from tqdm import tqdm


class COVID19Spreadsheet:
    def __init__(self, credentials_filename, spreadsheet_id):
        with open(credentials_filename) as fobj:
            credentials = json.load(fobj)
        self.account = ServiceAccountCredentials.from_json_keyfile_dict(credentials)
        self.client = gspread.authorize(self.account)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)

    @property
    def state_data(self):
        return self.spreadsheet.worksheet("Sheet1").get_all_records()

    @property
    def diff_states(self):
        header = [
            "today_date",
            "today_state",
            "today_data_dados",
            "today_confirmed",
            "today_deaths",
            "today_vaccination",
            "empty_1",
            "yesterday_state",
            "yesterday_date",
            "yesterday_data_dados",
            "yesterday_confirmed",
            "yesterday_deaths",
            "yesterday_vaccination",
            "empty_2",
            "novos_casos",
            "novos_casos_percent",
            "novas_mortes",
            "novas_mortes_percent",
            "novos_vacinados",
            "novos_vacinados_percent",
            "diff_dias",
        ]
        result = []
        for row in self.spreadsheet.worksheet("diff_states").get("B4:V30"):
            row = dict(zip(header, row))
            for key, value in row.items():
                if "_percent" in key:
                    row[key] = rows.fields.PercentField.deserialize(value)
                elif key.endswith("_date") or "_data_" in key:
                    row[key] = rows.fields.DateField.deserialize(value)
                elif (
                    "_confirmed" in key
                    or "_deaths" in key
                    or "vaccination" in key
                    or "novos_" in key
                    or "novas_" in key
                    or key == "diff_dias"
                ):
                    row[key] = int(value) if value else None
            result.append(row)
        return result


def format_number_br(n):
    """
    >>> format_number_br(123)
    '123'
    >>> format_number_br(1234)
    '1.234'
    >>> format_number_br(1234.56)
    '1.234,56'
    >>> format_number_br(123456789.01)
    '123.456.789,01'
    """

    return f"{n:,}".replace(",", "X").replace(".", ",").replace("X", ".")


def abbreviate_number(n, divider=1_000, suffix=None):
    """
    >>> abbreviate_number(100)
    '100'
    >>> abbreviate_number(1_000)
    '1.0K'
    >>> abbreviate_number(1_000, divider=1_024)
    '1000'
    >>> abbreviate_number(1_024, divider=1_024)
    '1.0K'
    >>> abbreviate_number(1_024, divider=1_024, suffix="iB")
    '1.0KiB'
    >>> abbreviate_number(1_500)
    '1.5K'
    >>> abbreviate_number(10_000)
    '10.0K'
    >>> abbreviate_number(1_000_000)
    '1.0M'
    >>> abbreviate_number(1_234_000_000)
    '1.2G'
    >>> abbreviate_number(1_234_567_890_000)
    '1.2T'
    >>> abbreviate_number(1_234_567_890_000_123)
    '1.2P'
    """
    suffix = suffix if suffix is not None else ""
    multipliers = ["K", "M", "G", "T", "P"]
    multiplier = ""
    while n >= divider:
        n /= divider
        multiplier = multipliers.pop(0)
    if not multiplier:
        return str(n) + suffix
    else:
        return f"{n:.1f}{multiplier}" + suffix


def file_metadata(filename, chunk_size=8 * 1024 * 1024):
    hasher = hashlib.sha1()

    with open(filename, mode="rb") as fobj, tqdm(unit_scale=True, unit="B") as progress:
        finished = False
        while not finished:
            data = fobj.read(chunk_size)
            hasher.update(data)
            chunk_length = len(data)
            finished = chunk_length == 0
            progress.update(chunk_length)
        total_bytes = progress.n

    new_lines = 0
    with open_compressed(filename, mode="rb") as fobj, tqdm(unit_scale=True, unit="B") as progress:
        finished = False
        finish_with_new_line = False
        while not finished:
            data = fobj.read(chunk_size)
            new_lines += data.count(b"\n")
            chunk_length = len(data)
            finished = chunk_length == 0
            if not finished:
                finish_with_new_line = data[-1] == b"\n"
            progress.update(chunk_length)
        uncompressed_bytes = progress.n
        if not finish_with_new_line:
            new_lines += 1

    return hasher.hexdigest(), new_lines, total_bytes, uncompressed_bytes


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("tweet_type", choices=["boletim", "vacinacao"])
    args = parser.parse_args()

    if args.tweet_type == "boletim":
        credentials_filename = "credentials/credentials-brasil-io-covid19.json"
        spreadsheet_id = os.environ["BULLETIN_SPREADSHEET_ID"]
        spreadsheet = COVID19Spreadsheet(credentials_filename, spreadsheet_id)

        start_date = datetime.date(2020, 6, 6)
        today = datetime.datetime.now().date()
        number = (today - start_date).days + 1

        state_data = spreadsheet.state_data
        total_confirmed = sum(row["confirmed"] for row in state_data)
        total_deaths = sum(row["deaths"] for row in state_data)
        all_bulletins_published_today = set(row["data_boletim"] for row in state_data) == {str(today)}
        if all_bulletins_published_today:
            pass
        else:
            missing_bulletins = [state for state in state_data if state["data_boletim"] != str(today)]
            missing_bulletins_text = [
                f"* Nem todos os estados liberaram boletins hoje, falta{'m' if len(missing_bulletins) > 1 else ''}:"
            ]
            for state in missing_bulletins:
                ms = state["MS"] in ("sim", "parcial")
                missing_bulletins_text.append(
                    f"- {state['state']}: {'usamos dados do @minsaude' if ms else 'sem dados hoje'}"
                )

        diff_states = spreadsheet.diff_states
        new_confirmed = sum(row["novos_casos"] for row in diff_states)
        new_deaths = sum(row["novas_mortes"] for row in diff_states)
        top_increase_deaths = []
        diff_states.sort(key=lambda row: row["novas_mortes_percent"], reverse=True)
        for state in diff_states[:5]:
            state_new_deaths = format_number_br(state["novas_mortes"])
            state_new_deaths_percent = (state["novas_mortes_percent"] * 100).quantize(Decimal("0.01"))
            top_increase_deaths.append(
                f"- {state['today_state']}: +{state_new_deaths.rjust(3)} ({format_number_br(state_new_deaths_percent)}%)"
            )
        top_increase_confirmed = []
        diff_states.sort(key=lambda row: row["novos_casos_percent"], reverse=True)
        for state in diff_states[:5]:
            state_new_confirmed_percent = (state["novos_casos_percent"] * 100).quantize(Decimal("0.01"))
            top_increase_confirmed.append(
                f"- {state['today_state']}: +{format_number_br(state_new_confirmed_percent)}%"
            )

        with open("boletim_template.txt") as fobj:
            template = Template(fobj.read())
        text = template.substitute(
            number=number,
            date=f"{today.day:02d}/{today.month:02d}",
            total_confirmed=format_number_br(total_confirmed),
            new_confirmed=format_number_br(new_confirmed),
            total_deaths=format_number_br(total_deaths),
            new_deaths=format_number_br(new_deaths),
            top_increase_deaths="\n".join(top_increase_deaths),
            top_increase_confirmed="\n".join(top_increase_confirmed),
            missing_bulletins="\n".join(missing_bulletins_text),
        )
        print(text)

    elif args.tweet_type == "vacinacao":
        filename = "data/output/microdados_vacinacao.csv.gz"
        sha1, lines, total_bytes, uncompressed_bytes = file_metadata(filename)
        file_size = abbreviate_number(total_bytes, suffix="B", divider=1_024)
        url = "https://data.brasil.io/dataset/covid19/microdados_vacinacao.csv.gz"
        print(
            "🎲 Acabamos de atualizar o CSV com microdados de vacinados, "
            f"agora com {format_number_br(lines - 1)} registros! "
            f"Baixe em: {url}\n"
            f"({file_size}, SHA1: {sha1})\n"
            f"#covid19 #OpenData"
        )


if __name__ == "__main__":
    main()
