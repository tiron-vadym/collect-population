import asyncio

import requests

from population.config import USER_AGENT, get_data_source_url


class HtmlDownloader:
    async def download(self, source: str | None = None) -> str:
        url = get_data_source_url(source)
        return await asyncio.to_thread(self._download_sync, url)

    @staticmethod
    def _download_sync(url: str) -> str:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        response.raise_for_status()
        return response.text
