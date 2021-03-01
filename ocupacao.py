import argparse
import datetime
from pathlib import Path

from rows.utils import CsvLazyDictWriter
from tqdm import tqdm

from covid19br.elasticsearch import ElasticSearch

DOWNLOAD_PATH = Path(__file__).parent / "data" / "ocupacao"
if not DOWNLOAD_PATH.exists():
    DOWNLOAD_PATH.mkdir(parents=True)

FIELD_CONVERTERS = {
    "estado": {"name": "", "converter": ""},
    "estadoSigla": {"name": "", "converter": ""},
    "municipio": {"name": "", "converter": ""},
    "cnes": {"name": "", "converter": ""},
    "dataNotificacaoOcupacao": {"name": "", "converter": ""},
    "ocupHospCli": {"name": "", "converter": ""},
    "ocupHospUti": {"name": "", "converter": ""},
    "ocupSRAGCli": {"name": "", "converter": ""},
    "ocupSRAGUti": {"name": "", "converter": ""},
    "altas": {"name": "", "converter": ""},
    "obitos": {"name": "", "converter": ""},
    "ocupacaoInformada": {"name": "", "converter": ""},
    "algumaOcupacaoInformada": {"name": "", "converter": ""},
    "nomeCnes": {"name": "", "converter": ""},
    "ofertaRespiradores": {"name": "", "converter": ""},
    "ofertaHospCli": {"name": "", "converter": ""},
    "ofertaHospUti": {"name": "", "converter": ""},
    "ofertaSRAGCli": {"name": "", "converter": ""},
    "ofertaSRAGUti": {"name": "", "converter": ""},
}


def convert_row(row):
    return {key: row.get(key, None) for key in FIELD_CONVERTERS.keys()}
    # TODO: implement

    # TODO: check municipio (correct name)
    #    return {
    #        "uf": row["estadoSigla"].upper(),
    #        "municipio": row["municipio"],
    #        "codigo_cnes": row["cnes"],
    #        "nome": row["nomeCnes"],
    #        'dataNotificacaoOcupacao': '2020-08-11T03:00:07.102Z',
    #        'ofertaRespiradores': 0,
    #        'ofertaHospCli': 86,
    #        'ofertaHospUti': 0,
    #        'ofertaSRAGCli': 12,
    #        'ofertaSRAGUti': 0,
    #        'ocupHospCli': 22,
    #        'ocupHospUti': 3,
    #        'ocupSRAGCli': 2,
    #        'ocupSRAGUti': 3,
    #        'altas': 0,
    #        'obitos': 1,
    #        'ocupacaoInformada': True,
    #        'algumaOcupacaoInformada': True
    #    }

    return row


def main():
    dt = datetime.datetime.today().strftime("%Y-%m-%dT%H:%M:%S")

    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="user-api-leitos")
    parser.add_argument("--password", default="aQbLL3ZStaTr38tj")
    parser.add_argument("--api-url", default="https://elastic-leitos.saude.gov.br/")
    parser.add_argument("--index", default="leito_ocupacao")
    parser.add_argument("--ttl", default="10m")
    parser.add_argument("--output-filename", default=DOWNLOAD_PATH / f"ocupacao-{dt}.csv")
    args = parser.parse_args()

    es = ElasticSearch(args.api_url)
    iterator = es.paginate(
        index=args.index, sort_by="dataNotificacaoOcupacao", user=args.username, password=args.password, ttl=args.ttl,
    )

    writer = CsvLazyDictWriter(args.output_filename)
    progress = tqdm(unit_scale=True)
    for page_number, page in enumerate(iterator, start=1):
        progress.desc = f"Downloading page {page_number}"
        for row in page["hits"]["hits"]:
            writer.writerow(convert_row(row["_source"]))
            progress.update()
    writer.close()


if __name__ == "__main__":
    main()
