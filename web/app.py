import csv

from flask import Flask, make_response

from web.spiders import run_state_spider, STATE_SPIDERS


app = Flask(__name__)


@app.route("/")
def index():
    spider_links = "\n".join(
        f'<li> <a href="/{state}">{state}</a> </li>' for state in STATE_SPIDERS
    )
    return f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Brasil.IO COVID-19 Spiders</title>
      </head>
      <body>
        <ul>
          {spider_links}
        </ul>
      </body>
    </html>
    """


def get_spider_response(state):
    status, response = run_state_spider(state)
    if status == "error":
        return make_response(f"Error while running spider: {response}", 500)

    report_fobj, case_fobj = response
    reports = list(csv.DictReader(report_fobj))
    if not reports:
        return make_response(f"Could not find any report (see spider logs)", 500)

    date = reports[0]["date"]
    # TODO: do something with reports

    response = make_response(case_fobj.getvalue())
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename=caso-{state}-{date}.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route("/<state>")
def get_state_csv(state):
    state = state.upper().strip()
    if state not in STATE_SPIDERS:
        return "State not found", 404

    return get_spider_response(state)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
