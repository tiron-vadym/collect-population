from __future__ import annotations

import asyncio
from typing import List, Tuple

import psycopg

from population.config import PostgresConfig, get_data_source
from population.models import CountryPopulation

RegionSummaryRow = Tuple[str, int, str, int, str, int]


class PopulationRepository:
    REGION_SUMMARY_QUERY = """
        WITH ranked AS (
            SELECT
                region,
                country_name,
                population,
                ROW_NUMBER() OVER (PARTITION BY region ORDER BY population DESC) AS largest_rank,
                ROW_NUMBER() OVER (PARTITION BY region ORDER BY population ASC) AS smallest_rank
            FROM country_population
            WHERE source = %s
        )
        SELECT
            region,
            SUM(population) AS total_population,
            MAX(CASE WHEN largest_rank = 1 THEN country_name END) AS largest_country_name,
            MAX(CASE WHEN largest_rank = 1 THEN population END) AS largest_country_population,
            MAX(CASE WHEN smallest_rank = 1 THEN country_name END) AS smallest_country_name,
            MAX(CASE WHEN smallest_rank = 1 THEN population END) AS smallest_country_population
        FROM ranked
        GROUP BY region
        ORDER BY region
    """

    def __init__(self, config: PostgresConfig | None = None) -> None:
        self.config = config or PostgresConfig.from_env()

    async def connect(self):
        for attempt in range(20):
            try:
                return await psycopg.AsyncConnection.connect(
                    host=self.config.host,
                    port=self.config.port,
                    dbname=self.config.database,
                    user=self.config.user,
                    password=self.config.password,
                )
            except psycopg.OperationalError:
                if attempt == 19:
                    raise
                await asyncio.sleep(2)

        raise RuntimeError("Unable to connect to PostgreSQL")

    async def create_schema(self) -> None:
        async with await self.connect() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS country_population (
                        id SERIAL PRIMARY KEY,
                        country_name TEXT NOT NULL,
                        region TEXT NOT NULL,
                        population BIGINT NOT NULL,
                        source TEXT NOT NULL,
                        population_year TEXT NOT NULL
                    )
                    """
                )
                await connection.commit()

    async def clear_source_data(self, source: str) -> None:
        async with await self.connect() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("DELETE FROM country_population WHERE source = %s", (source,))
                await connection.commit()

    async def save_rows(self, rows: List[CountryPopulation]) -> None:
        if not rows:
            return

        async with await self.connect() as connection:
            async with connection.cursor() as cursor:
                await cursor.executemany(
                    """
                    INSERT INTO country_population (country_name, region, population, source, population_year)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [
                        (row.country_name, row.region, row.population, row.source, row.population_year)
                        for row in rows
                    ],
                )
                await connection.commit()

    async def fetch_region_summary(self, source: str | None = None) -> List[RegionSummaryRow]:
        selected_source = source or get_data_source()
        async with await self.connect() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(self.REGION_SUMMARY_QUERY, (selected_source,))
                return await cursor.fetchall()
