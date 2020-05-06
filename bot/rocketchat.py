#!/usr/bin/env python
from urllib.parse import urljoin

import requests

HTTP_METHODS = "GET HEAD POST PUT DELETE CONNECT OPTIONS TRACE PATCH".lower().split()


class RocketChat:
    def __init__(self, base_url):
        self.base_url = base_url

    def make_url(self, endpoint):
        return urljoin(self.base_url, f"/api/v1/{endpoint}")

    def make_request(self, method, *args, **kwargs):
        method = method.lower().strip()
        assert method in HTTP_METHODS

        kwargs["headers"] = kwargs.get("headers", {})
        kwargs["headers"]["X-Auth-Token"] = self.auth_token
        kwargs["headers"]["X-User-Id"] = self.user_id
        return getattr(requests, method)(*args, **kwargs)

    def login(self, username, password):
        self.username = username
        response = requests.post(
            self.make_url("login"), data={"user": username, "password": password}
        )
        data = response.json()
        assert data["status"] == "success"
        self.user_id = data["data"]["userId"]
        self.auth_token = data["data"]["authToken"]
        self.user_data = data["data"]["me"]

    def create_bot_user(self, bot_username, bot_password, bot_email, bot_name):
        return self.make_request(
            "POST",
            self.make_url("users.create"),
            json={
                "username": bot_username,
                "password": bot_password,
                "email": bot_email,
                "name": bot_name,
                "active": True,
                "roles": ["bot"],
                "joinDefaultChannels": False,
                "requirePasswordChange": False,
                "sendWelcomeEmail": False,
                "verified": True,
            },
        )

    def send_message(self, channel, message):
        return self.make_request(
            "POST",
            self.make_url("chat.postMessage"),
            json={"channel": channel, "text": message,},
        )


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("--base_url")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--user_id")
    parser.add_argument("--auth_token")
    parser.add_argument("channel")
    parser.add_argument("message")
    args = parser.parse_args()

    base_url = args.base_url or os.environ["ROCKETCHAT_BASE_URL"]

    username = args.username or os.environ.get("ROCKETCHAT_USERNAME")
    password = args.password or os.environ.get("ROCKETCHAT_PASSWORD")
    user_id = args.user_id or os.environ.get("ROCKETCHAT_USER_ID")
    auth_token = args.auth_token or os.environ.get("ROCKETCHAT_AUTH_TOKEN")
    if (
        (username, password, user_id, auth_token) == (None, None, None, None)
        or (username and not password)
        or (user_id and not auth_token)
    ):
        print("ERROR: must pass username and password or user_id and auth_token")
        exit(1)

    chat = RocketChat(base_url)
    if username and password:
        chat.login(username, password)
    elif user_id and auth_token:
        chat.user_id = user_id
        chat.auth_token = auth_token
    else:
        print("ERROR: cannot authenticate")
        exit(2)
    chat.send_message(args.channel, args.message)
