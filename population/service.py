import asyncio

from population.config import get_data_source
from population.downloader import HtmlDownloader
from population.parsers import DataParser
from population.repository import PopulationRepository


class PopulationService:
    def __init__(
        self,
        parser: DataParser,
        repository: PopulationRepository,
        downloader: HtmlDownloader | None = None,
    ) -> None:
        self.parser = parser
        self.repository = repository
        self.downloader = downloader or HtmlDownloader()

    async def load_data(self) -> None:
        source = get_data_source()
        await self.repository.create_schema()
        await self.repository.clear_source_data(source)
        html = await self.downloader.download(source)
        rows = self.parser.parse(html)
        await self.repository.save_rows(rows)

    async def print_summary(self) -> None:
        rows = await self.repository.fetch_region_summary()
        for (
            region,
            total_population,
            largest_country_name,
            largest_country_population,
            smallest_country_name,
            smallest_country_population,
        ) in rows:
            print(region)
            print(total_population)
            print(largest_country_name)
            print(largest_country_population)
            print(smallest_country_name)
            print(smallest_country_population)
            print()

    def load_data_sync(self) -> None:
        asyncio.run(self.load_data())

    def print_summary_sync(self) -> None:
        asyncio.run(self.print_summary())
