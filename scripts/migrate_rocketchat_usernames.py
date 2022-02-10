import argparse
import os
import re

import rows
from tqdm import tqdm

from bot.rocketchat import RocketChat

USERNAME_REGEXP = re.compile(r"[^A-Za-z0-9_]")
PUNCT_REGEXP = re.compile("[-/ .]")


def is_valid_username(username):
    return not (
        PUNCT_REGEXP.sub("", username).isdigit() or USERNAME_REGEXP.search(username)
    )


def usernames_suggestions(email, name):
    suggestions = []
    if email:
        suggestions.append(rows.utils.slug(email.split("@")[0]))
    if name:
        suggestions.append(rows.utils.slug(name))

    return suggestions + [f"{s}_{n}" for s in suggestions for n in range(1, 3)]


def create_row(user_data, suggestion):
    return {
        "user_id": user_data["user_id"],
        "old_username": user_data["username"],
        "new_username": suggestion,
        "email": user_data["email"],
    }


def migrate(output_filename, commit):
    rocket_chat = RocketChat(os.environ["ROCKETCHAT_BASE_URL"])
    rocket_chat.login(
        os.environ["ROCKETCHAT_USERNAME"], os.environ["ROCKETCHAT_PASSWORD"]
    )
    all_users = rocket_chat.user_list()

    existing_usernames = set()
    users_data = []
    for user in tqdm(all_users, desc="Baixando informações dos usuários..."):
        data = {
            "user_id": user["_id"],
            "username": user.get("username"),
            "name": user.get("name"),
        }
        data["email"] = user.get("emails", [{"address": None}])[0]["address"]
        data["is_valid"] = is_valid_username(data["username"] or ".")
        users_data.append(data)
        existing_usernames.add(data["username"])

    with open(output_filename, "w") as csvfile:
        writer = rows.utils.CsvLazyDictWriter(csvfile)

        invalid_users = [u for u in users_data if not u["is_valid"]]
        for invalid_user in tqdm(invalid_users, desc="Atulizando usernames inválidos"):
            suggestions = usernames_suggestions(
                invalid_user["email"], invalid_user["name"]
            )
            for suggestion in suggestions:
                if suggestion not in existing_usernames:
                    existing_usernames.add(suggestion)
                    if commit:
                        rocket_chat.user_update(
                            invalid_user["user_id"], {"username": suggestion}
                        )
                    writer.writerow(create_row(invalid_user, suggestion))
                    break
        else:
            import sys

            print(
                f"Cannot change user (suggestions already used): {invalid_user}",
                file=sys.stderr,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_filename")
    parser.add_argument(
        "--commit",
        default=False,
        action="store_true",
        help="Se esta flag for passada o script irá atualizar os dados na API",
    )
    args = parser.parse_args()
    data = migrate(args.output_filename, args.commit)
