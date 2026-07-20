import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(override=False)


@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: str
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "PostgresConfig":
        return cls(
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "population"),
            user=os.getenv("POSTGRES_USER", "population"),
            password=os.getenv("POSTGRES_PASSWORD", "population"),
        )


DATA_SOURCE_URLS = {
    "wikipedia": (
        "https://en.wikipedia.org/w/index.php?"
        "title=List_of_countries_by_population_(United_Nations)&oldid=1215058959"
    ),
    "statisticstimes": "https://statisticstimes.com/demographics/countries-by-population.php",
    "worldometers": "https://www.worldometers.info/world-population/population-by-country/",
}

DEFAULT_DATA_SOURCE = "wikipedia"
USER_AGENT = "CollectPopulation/1.0 (population data collector; educational project)"


def get_data_source() -> str:
    return os.getenv("DATA_SOURCE", DEFAULT_DATA_SOURCE).lower()


def get_data_source_url(source: str | None = None) -> str:
    selected_source = source or get_data_source()
    try:
        return DATA_SOURCE_URLS[selected_source]
    except KeyError as exc:
        supported = ", ".join(sorted(DATA_SOURCE_URLS))
        raise ValueError(f"Unsupported DATA_SOURCE: {selected_source}. Supported: {supported}") from exc
