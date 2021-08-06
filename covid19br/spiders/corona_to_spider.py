# Para esse script funcionar, você precisa instalar as dependências:
# pip install -U https://github.com/turicas/rows/archive/develop.zip pymupdf cached-property
import argparse
import re
import unicodedata
from collections import defaultdict

import rows


def unaccent(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", errors="ignore").decode("ascii")


def extract_tables(objs):
    """Extrai as tabelas contidas nos objetos"""

    # Pega posição x do meio dos títulos (cabeçalhos) das tabelas
    cities_boundaries, values_boundaries = [], []
    for obj in sorted(objs, key=lambda obj: (obj.y0, obj.x0)):
        if obj.text == "MUNICÍPIO":
            cities_boundaries.append(int(obj.x0 + (obj.x1 - obj.x0) / 2))
        elif obj.text == "TOTAL":
            values_boundaries.append(int(obj.x0 + (obj.x1 - obj.x0) / 2))
    # Como são 2 colunas (1 com pelo menos 1 tabela), devemos pegar as
    # coordenadas da tabela mais à esquerda e da mais à direita:
    first_cities, last_cities = min(cities_boundaries), max(cities_boundaries)
    first_values, last_values = min(values_boundaries), max(values_boundaries)

    # Organiza os objetos em lista de municípios e valor numérico, de acordo
    # com suas posições x
    cities, values = [], []
    for obj in objs:
        if obj.x0 < first_cities < obj.x1 or obj.x0 < last_cities < obj.x1:
            cities.append(obj)
        elif obj.x0 < first_values < obj.x1 or obj.x0 < last_values < obj.x1:
            values.append(obj)

    # Ordena os objetos selecionados a partir de (y0, x0)
    obj_sort = lambda obj: (obj.y0, obj.x0)
    cities.sort(key=obj_sort)
    values.sort(key=obj_sort)

    # Encontra qual o y0 do objeto mais ao topo da página
    first_y0 = min(obj.y0 for obj in cities if obj.text == "MUNICÍPIO")

    # Remove todos os objetos texto que não sejam valores de interesse (tanto
    # os que podem estar fora das tabelas, quanto os cabeçalhos e valores
    # "fantasma" - números que aparecem invisíveis atrás da tabela) e guarda os
    # nomes de municípios sem acento (às vezes aparecem com acento, às vezes,
    # sem, muitas vezes no mesmo PDF).
    clean_cities = [
        unaccent(obj.text)
        for obj in cities
        if obj.y0 > first_y0 and obj.text != "MUNICÍPIO" and not obj.text.isdigit()
    ]
    clean_values = [
        int(obj.text.replace(".", ""))
        for obj in values
        if obj.y0 > first_y0 and obj.text != "TOTAL"
    ]
    for city, value in zip(clean_cities, clean_values):
        if city == "TOTAL":
            # Elimina o último registro da tabela, que contém o total
            continue
        yield (city, value)


def pdf_to_csv(pdf_filename, csv_filename):
    """Converte PDF do boletim COVID-19 do Tocantins em CSV"""

    writer = rows.utils.CsvLazyDictWriter(csv_filename)
    doc = rows.plugins.pdf.PyMuPDFBackend(pdf_filename)
    table = defaultdict(dict)
    total = {"confirmed": 0, "deaths": 0}
    # Percorre todas as páginas e identifica qual a página dos casos
    # confirmados e óbitos, para então extrair as tabelas.
    for page_number in range(1, rows.plugins.pdf.number_of_pages(pdf_filename) + 1):
        objs = list(next(doc.text_objects(page_numbers=(page_number,))))
        page_text = "\n".join(obj.text for obj in objs)
        if "Distribuição dos casos confirmados acumulados" in page_text:
            # Página contém casos confirmados
            key = "confirmed"
        elif "Distribuição dos óbitos confirmados acumulados" in page_text:
            # Página contém óbitos confirmados
            key = "deaths"
        else:
            continue

        for city, value in extract_tables(objs):
            table[city][key] = value
            total[key] += value

    writer.writerow(
        {
            "municipio": "TOTAL NO ESTADO",
            "confirmados": total["confirmed"],
            "obitos": total["deaths"],
        }
    )
    for city, values in sorted(table.items()):
        writer.writerow(
            {
                "municipio": city,
                "confirmados": values["confirmed"],
                "obitos": values.get("deaths", 0),
            }
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_filename")
    parser.add_argument("csv_filename")
    args = parser.parse_args()

    pdf_to_csv(args.pdf_filename, args.csv_filename)
