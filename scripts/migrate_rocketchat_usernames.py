import argparse
import os
import re

from tqdm import tqdm

from bot.rocketchat import RocketChat


USERNAME_REGEXP = re.compile(r"[^A-Za-z0-9_]")
PUNCT_REGEXP = re.compile("[-/ .]")


def is_valid_username(username):
    return not (PUNCT_REGEXP.sub("", username).isdigit() or USERNAME_REGEXP.search(username))


def migrate(output_filename):
    rocket_chat = RocketChat(os.environ["ROCKETCHAT_BASE_URL"])
    rocket_chat.login(
        os.environ["ROCKETCHAT_USERNAME"],
        os.environ["ROCKETCHAT_PASSWORD"]
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

    invalid_users = [u for u in users_data if not u["is_valid"]]
    for invalid_user in invalid_users:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_filename")
    args = parser.parse_args()
    data = migrate(args.ouput_filename)
