from population.config import get_data_source
from population.parsers import DataParser, StatisticsTimesParser, WikipediaParser, WorldometersParser


def build_parser(source: str | None = None) -> DataParser:
    selected_source = source or get_data_source()
    if selected_source == "wikipedia":
        return WikipediaParser()
    if selected_source == "statisticstimes":
        return StatisticsTimesParser()
    if selected_source == "worldometers":
        return WorldometersParser()
    raise ValueError(f"Unsupported DATA_SOURCE: {selected_source}")
