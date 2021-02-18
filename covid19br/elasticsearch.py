from urllib.parse import urljoin

import requests


class ElasticSearch:
    def __init__(self, base_url, user_agent=None):
        self.base_url = base_url
        self.user_agent = user_agent

    def paginate(self, index, sort_by, user=None, password=None, page_size=10_000, ttl="10m"):
        session = requests.Session()
        if self.user_agent is not None:
            session.headers["User-Agent"] = self.user_agent
        if user is not None and password is not None:
            session.auth = (user, password)

        index_url = urljoin(self.base_url, index)
        url = urljoin(index_url, "_search")
        params = {
            "sort": sort_by,
            "size": page_size,
            "scroll": ttl,
        }

        # Get first page
        response = session.get(url, params=params)
        response_data = response.json()
        yield response_data

        # Then, paginate
        finished = False
        while not finished:
            url = urljoin(self.base_url, "_search/scroll")
            params = {"scroll": ttl, "scroll_id": response_data["_scroll_id"]}
            response = session.get(url, params=params)
            response_data = response.json()
            yield response_data
            finished = (
                "hits" not in response_data.get("hits", {}) or len(response_data.get("hits", {}).get("hits", [])) == 0
            )
