from __future__ import annotations

import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import psycopg
import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class CountryPopulation:
    country_name: str
    region: str
    population: int
    source: str
    population_year: str


class DataParser(ABC):
    @abstractmethod
    def parse(self, html: str) -> List[CountryPopulation]:
        raise NotImplementedError


class WikipediaParser(DataParser):
    def parse(self, html: str) -> List[CountryPopulation]:
        soup = BeautifulSoup(html, "html.parser")
        table = None
        for candidate in soup.find_all("table"):
            headers = [cell.get_text(" ", strip=True) for cell in candidate.find_all(["th", "td"])[:6]]
            if headers and "Country or territory" in headers[0]:
                table = candidate
                break
        if table is None:
            raise ValueError("Wikipedia table was not found")

        rows: List[CountryPopulation] = []
        for row in table.find_all("tr")[1:]:
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
            if len(cells) < 6:
                continue
            country_name = self._clean_text(cells[0])
            if not country_name or country_name.lower() == "world":
                continue
            population = self._parse_population(cells[2])
            region = self._clean_text(cells[4])
            if not population or not region:
                continue
            rows.append(
                CountryPopulation(
                    country_name=country_name,
                    region=region,
                    population=population,
                    source="wikipedia",
                    population_year="2023",
                )
            )
        return rows

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()

    @staticmethod
    def _parse_population(value: str) -> Optional[int]:
        cleaned = re.sub(r"[^0-9]", "", value)
        return int(cleaned) if cleaned else None


class StatisticsTimesParser(DataParser):
    def parse(self, html: str) -> List[CountryPopulation]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", id="table_id")
        if table is None:
            raise ValueError("Statistics Times table was not found")

        rows: List[CountryPopulation] = []
        for row in table.find_all("tr")[2:]:
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
            if len(cells) < 9:
                continue
            country_name = self._clean_text(cells[0])
            if not country_name or country_name.lower() == "country/region":
                continue
            population = self._parse_population(cells[3])
            region = self._clean_text(cells[8])
            if not population or not region:
                continue
            rows.append(
                CountryPopulation(
                    country_name=country_name,
                    region=region,
                    population=population,
                    source="statisticstimes",
                    population_year="2025",
                )
            )
        return rows

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()

    @staticmethod
    def _parse_population(value: str) -> Optional[int]:
        cleaned = re.sub(r"[^0-9]", "", value)
        return int(cleaned) if cleaned else None


class PopulationRepository:
    def __init__(self) -> None:
        self.host = os.getenv("POSTGRES_HOST", "postgres")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.database = os.getenv("POSTGRES_DB", "population")
        self.user = os.getenv("POSTGRES_USER", "population")
        self.password = os.getenv("POSTGRES_PASSWORD", "population")

    def connect(self):
        for attempt in range(20):
            try:
                return psycopg.connect(
                    host=self.host,
                    port=self.port,
                    dbname=self.database,
                    user=self.user,
                    password=self.password,
                )
            except psycopg.OperationalError:
                if attempt == 19:
                    raise
                time.sleep(2)

        raise RuntimeError("Unable to connect to PostgreSQL")

    def create_schema(self) -> None:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
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
                connection.commit()

    def clear_data(self) -> None:
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE country_population RESTART IDENTITY")
                connection.commit()

    def save_rows(self, rows: List[CountryPopulation]) -> None:
        if not rows:
            return
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO country_population (country_name, region, population, source, population_year)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    [(row.country_name, row.region, row.population, row.source, row.population_year) for row in rows],
                )
                connection.commit()

    def fetch_region_summary(self):
        with self.connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    WITH ranked AS (
                        SELECT
                            region,
                            country_name,
                            population,
                            ROW_NUMBER() OVER (PARTITION BY region ORDER BY population DESC) AS largest_rank,
                            ROW_NUMBER() OVER (PARTITION BY region ORDER BY population ASC) AS smallest_rank
                        FROM country_population
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
                )
                return cursor.fetchall()


class PopulationService:
    def __init__(self, parser: DataParser, repository: PopulationRepository) -> None:
        self.parser = parser
        self.repository = repository

    def load_data(self) -> None:
        self.repository.create_schema()
        self.repository.clear_data()
        html = self._download_html()
        rows = self.parser.parse(html)
        self.repository.save_rows(rows)

    def print_summary(self) -> None:
        rows = self.repository.fetch_region_summary()
        for region, total_population, largest_country_name, largest_country_population, smallest_country_name, smallest_country_population in rows:
            print(region)
            print(f"Total population: {total_population}")
            print(f"Largest country: {largest_country_name}")
            print(f"Largest population: {largest_country_population}")
            print(f"Smallest country: {smallest_country_name}")
            print(f"Smallest population: {smallest_country_population}")
            print()

    def _download_html(self) -> str:
        source = os.getenv("DATA_SOURCE", "wikipedia").lower()
        if source == "wikipedia":
            url = "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_population_(United_Nations)"
        elif source == "statisticstimes":
            url = "https://statisticstimes.com/demographics/countries-by-population.php"
        else:
            raise ValueError(f"Unsupported DATA_SOURCE: {source}")

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text


def build_parser() -> DataParser:
    source = os.getenv("DATA_SOURCE", "wikipedia").lower()
    if source == "wikipedia":
        return WikipediaParser()
    if source == "statisticstimes":
        return StatisticsTimesParser()
    raise ValueError(f"Unsupported DATA_SOURCE: {source}")


def main() -> None:
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: main.py <get_data|print_data>")

    command = sys.argv[1]
    service = PopulationService(build_parser(), PopulationRepository())
    if command == "get_data":
        service.load_data()
    elif command == "print_data":
        service.print_summary()
    else:
        raise SystemExit("Usage: main.py <get_data|print_data>")
