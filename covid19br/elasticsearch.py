from urllib.parse import urljoin

import requests
from async_process_executor import AsyncProcessExecutor, Task
from rows.utils import CsvLazyDictWriter
from tqdm import tqdm


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


class ElasticSearchConsumer(AsyncProcessExecutor):
    def __init__(
        self,
        api_url,
        index_name,
        sort_by,
        convert_function,
        output_filename,
        username=None,
        password=None,
        ttl="10m",
        progress=True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.convert_function = convert_function
        self.es = ElasticSearch(api_url)
        self.iterator = self.es.paginate(index=index_name, sort_by=sort_by, user=username, password=password, ttl=ttl,)
        self.writer = CsvLazyDictWriter(output_filename)
        self.show_progress = progress
        if self.show_progress:
            self.progress = tqdm(unit_scale=True)

    async def tasks(self):
        if self.show_progress:
            self.progress.desc = f"Downloading page 001"
            self.progress.refresh()

        for page_number, page in enumerate(self.iterator, start=1):
            if self.show_progress:
                self.progress.desc = f"Downloaded page {page_number:03d}"
                self.progress.refresh()

            yield Task(function=self.convert_function, args=(page,))

    async def process(self, result):
        for row in result:
            self.writer.writerow(row)
            if self.show_progress:
                self.progress.update()

    async def finsihed(self):
        if self.show_progress:
            self.progress.close()
