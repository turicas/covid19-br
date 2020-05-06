import getpass
import io
from collections import defaultdict
from urllib.request import urlopen

import rows
from tqdm import tqdm

import rocketchat

your_username = "fill-your-username-here"
your_password = getpass.getpass()
spreadsheet_id = "1S77CvorwQripFZjlWTOZeBhK42rh3u57aRL1XZGhSdI"

chat = rocketchat.RocketChat("https://chat.brasil.io/")
chat.login(your_username, your_password)

url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv#gid=0"
csv_data = urlopen(url).read()
table = rows.import_from_csv(io.BytesIO(csv_data), encoding="utf-8")
username_correto = {}
voluntarios = defaultdict(list)
voluntarios_uf = defaultdict(list)
for row in table:
    uf = row.uf.upper().strip()
    for voluntario in row.voluntarios.split(","):
        voluntario = voluntario.strip()
        username_correto[voluntario.lower()] = voluntario
        voluntarios_uf[uf].append(voluntario.lower())
    for voluntario in voluntarios_uf[uf]:
        voluntarios[voluntario].append(uf)
template = """
...your message here...
<ESTADOS>
""".strip()

progress = tqdm(voluntarios.items(), desc=" " * 25)
for username, estados in progress:
    progress.desc = username.center(25)
    responsaveis = {
        estado: ", ".join(
            f"@{username_correto[v]}" for v in voluntarios_uf[estado] if v != username
        )
        for estado in estados
    }
    estados_str = []
    for estado in estados:
        outros = responsaveis[estado]
        if not outros:
            outros = "(por enquanto só tem você nesse estado =/)"
        else:
            outros = f"(em conjunto com {outros})"
        estados_str.append(f"- *{estado}* {outros}")
    estados_str = "\n".join(estados_str)
    chat.send_message(
        f"@{username_correto[username]}", template.replace("<ESTADOS>", estados_str)
    )
