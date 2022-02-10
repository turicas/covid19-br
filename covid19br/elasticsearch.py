import json
import time
from urllib.parse import urljoin

import requests
from async_process_executor import AsyncProcessExecutor, Task
from rows.utils import CsvLazyDictWriter
from tqdm import tqdm


class GeneratorWithLength:
    def __init__(self, generator, length):
        self.__len = length
        self.__gen = generator

    def __len__(self):
        return self.__len

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.__gen)


class ElasticSearch:
    def __init__(
        self, base_url, username=None, password=None, user_agent=None, timeout=10
    ):
        self.base_url = base_url
        self.__username = username
        self.__password = password
        self.search_url = urljoin(self.base_url, "_search")
        self.timeout = timeout

        self.session = requests.Session()
        if user_agent is not None:
            self.session.headers["User-Agent"] = user_agent
        if username is not None and password is not None:
            self.session.auth = (username, password)

    def index_url(self, index):
        return urljoin(self.base_url, index)

    def search(self, index, sort_by, page_size=10_000, ttl="10m", query=None):
        """Search using scroll API"""

        if isinstance(sort_by, str):
            sort = [{sort_by: "asc"}]
        elif isinstance(sort_by, (list, tuple)):
            # expected format: [("field1", "asc"), ("field2", "desc"), ...]
            sort = list(sort_by)
        else:
            raise ValueError(f"Invalid type '{type(sort_by)}' for 'sort_by'")

        result = self.consume_scroll(index, sort, page_size, ttl, query)
        total_hits = next(result)
        return GeneratorWithLength(result, total_hits)

    def consume_scroll(
        self, index, sort, page_size, ttl, query, max_retries=5, wait_time=3
    ):
        body = {
            "query": query,
            "size": page_size,
            "sort": sort,
            "track_total_hits": True,
        }
        if not query:
            del body["query"]
        url = self.index_url(index) + "/_search"
        params = {"scroll": ttl}
        first_page = True
        while True:
            retries = 0
            while retries < max_retries:
                try:
                    response = self.session.post(
                        url, params=params, json=body, timeout=self.timeout
                    )
                    response_data = response.json()
                except json.decoder.JSONDecodeError:
                    print(f"\nERROR: cannot parse response as JSON: {response.content}")
                    retries += 1
                    time.sleep(wait_time)
                else:
                    break

            if first_page:
                yield response_data["hits"]["total"]["value"]
                url = self.base_url + "_search/scroll"
                params = {}
                body = {
                    "scroll": ttl,
                    "scroll_id": response_data["_scroll_id"],
                }
                first_page = False

            hits = response_data["hits"].pop("hits", [])
            if hits:
                for hit in hits:
                    yield hit["_source"]
            else:
                break


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
        self.es = ElasticSearch(
            api_url,
            username=username,
            password=password,
        )
        self.iterator = self.es.search(
            index=index_name,
            sort_by=sort_by,
            ttl=ttl,
        )
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
