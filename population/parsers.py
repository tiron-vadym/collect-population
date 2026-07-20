from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import List, Optional

from bs4 import BeautifulSoup

from population.models import CountryPopulation
from population.regions import lookup_region


class DataParser(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def parse(self, html: str) -> List[CountryPopulation]:
        raise NotImplementedError

    @staticmethod
    def _clean_text(value: str) -> str:
        cleaned = value.replace("\xa0", " ")
        cleaned = re.sub(r"\[\s*[^\]]+\s*\]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def _parse_population(value: str) -> Optional[int]:
        cleaned = re.sub(r"[^0-9]", "", value)
        return int(cleaned) if cleaned else None


class WikipediaParser(DataParser):
    source_name = "wikipedia"

    def parse(self, html: str) -> List[CountryPopulation]:
        soup = BeautifulSoup(html, "html.parser")
        table = self._find_table(soup)
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
            if population is None or not region:
                continue

            rows.append(
                CountryPopulation(
                    country_name=country_name,
                    region=region,
                    population=population,
                    source=self.source_name,
                    population_year="2023",
                )
            )
        return rows

    @staticmethod
    def _find_table(soup: BeautifulSoup):
        for candidate in soup.find_all("table"):
            header_row = candidate.find("tr")
            if header_row is None:
                continue
            headers = [cell.get_text(" ", strip=True) for cell in header_row.find_all(["th", "td"])]
            if headers and headers[0].startswith("Location"):
                return candidate
        return None


class StatisticsTimesParser(DataParser):
    source_name = "statisticstimes"

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
            if population is None or not region:
                continue

            rows.append(
                CountryPopulation(
                    country_name=country_name,
                    region=region,
                    population=population,
                    source=self.source_name,
                    population_year="2025",
                )
            )
        return rows


class WorldometersParser(DataParser):
    source_name = "worldometers"

    def parse(self, html: str) -> List[CountryPopulation]:
        soup = BeautifulSoup(html, "html.parser")
        table = self._find_table(soup)
        if table is None:
            raise ValueError("Worldometers table was not found")

        rows: List[CountryPopulation] = []
        for row in table.find_all("tr")[1:]:
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
            if len(cells) < 3:
                continue

            country_name = self._clean_text(cells[1])
            if not country_name or country_name.lower() == "country (or dependency)":
                continue

            population = self._parse_population(cells[2])
            region = lookup_region(country_name)
            if population is None or region is None:
                continue

            rows.append(
                CountryPopulation(
                    country_name=country_name,
                    region=region,
                    population=population,
                    source=self.source_name,
                    population_year="2026",
                )
            )
        return rows

    @staticmethod
    def _find_table(soup: BeautifulSoup):
        for candidate in soup.find_all("table"):
            header_row = candidate.find("tr")
            if header_row is None:
                continue
            headers = [cell.get_text(" ", strip=True) for cell in header_row.find_all(["th", "td"])]
            if headers and headers[0] == "#" and "Country" in headers[1]:
                return candidate
        return None
