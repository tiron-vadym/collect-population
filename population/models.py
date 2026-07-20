from dataclasses import dataclass


@dataclass(frozen=True)
class CountryPopulation:
    country_name: str
    region: str
    population: int
    source: str
    population_year: str
