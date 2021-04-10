import argparse
import os

import rows
import tqdm

from bot.rocketchat import RocketChat


def run(output_filename):
    rocket_chat = RocketChat(os.environ["ROCKETCHAT_BASE_URL"])
    rocket_chat.login(
        os.environ["ROCKETCHAT_USERNAME"],
        os.environ["ROCKETCHAT_PASSWORD"]
    )
    all_users = rocket_chat.user_list()
    with open(output_filename, "w") as csvfile:
        writer = rows.utils.CsvLazyDictWriter(csvfile)

        for user in tqdm.tqdm(all_users, desc="Buscando usuários não verificados..."):
            email = user.get("emails")
            if email:
                verified = email[0]["verified"]
                if verified is False:
                    writer.writerow(
                        {
                            "username": user.get("username"),
                            "name": user.get("name"),
                            "email": email[0].get("address"),
                        }
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_filename")
    args = parser.parse_args()
    run(args.output_filename)
