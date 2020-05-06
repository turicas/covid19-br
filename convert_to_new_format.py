import argparse

import rows

cities = rows.import_from_csv("data/populacao-estimada-2019.csv")


def convert(state, input_filename, output_filename):
    table = rows.import_from_csv(
        input_filename,
        force_types={
            "confirmed": rows.fields.IntegerField,
            "deaths": rows.fields.IntegerField,
        },
    )
    state_cities = ["TOTAL NO ESTADO", "Importados/Indefinidos"] + sorted(
        row.municipio for row in cities if row.uf == state
    )
    confirmed, deaths, dates = {}, {}, []
    for row in table:
        row_confirmed = row.confirmed or 0
        row_date = row.date
        row_deaths = row.deaths or 0
        row_name = row.city if row.place_type == "city" else "TOTAL NO ESTADO"

        if row_name not in state_cities:
            print(f"ERRO: município {repr(row_name)} não encontrado.")
            continue
        if row_confirmed == 0 and row_deaths == 0:
            # No data for this city in this day
            continue
        if row_date not in confirmed:
            confirmed[row_date] = {}
        if row_date not in deaths:
            deaths[row_date] = {}
        if row_name in confirmed[row_date] or row_name in deaths[row_date]:
            print(f"ERRO: conflito em {repr(row_name)} para {row_date}.")
            continue

        confirmed[row_date][row_name] = row_confirmed
        deaths[row_date][row_name] = row_deaths

    result = []
    dates = sorted(confirmed.keys(), reverse=True)
    for city in state_cities:
        row = {"municipio": city}
        for date in dates:
            date_str = f"{date.day:02d}_{date.month:02d}"
            row[f"confirmados_{date_str}"] = confirmed[date].get(city, None)
            row[f"mortes_{date_str}"] = deaths[date].get(city, None)
        result.append(row)
    rows.export_to_csv(rows.import_from_dicts(result), output_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("state")
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    convert(args.state, args.input_filename, args.output_filename)
