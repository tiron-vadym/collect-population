# Population data service

This project loads country population data from a public source into PostgreSQL, stores rows in unaggregated form (one row per country), and prints region-level summaries using a single SQL query.

## Run with Docker Compose

```bash
docker-compose up get_data
docker-compose up print_data
```

## Data sources

Copy `env.sample` to `.env` and adjust the values if needed. The database connection and `DATA_SOURCE` are loaded from environment variables.

Switch the parser and output source with the `DATA_SOURCE` environment variable:

- `wikipedia` (default) — [UN population list on Wikipedia](https://en.wikipedia.org/w/index.php?title=List_of_countries_by_population_(United_Nations)&oldid=1215058959)
- `statisticstimes` — [Statistics Times](https://statisticstimes.com/demographics/countries-by-population.php)
- `worldometers` — [Worldometers](https://www.worldometers.info/world-population/population-by-country/) (regions from `country_regions.json`)

Example:

```bash
cp env.sample .env
DATA_SOURCE=statisticstimes docker-compose up get_data
DATA_SOURCE=statisticstimes docker-compose up print_data
DATA_SOURCE=worldometers docker-compose up get_data
```

## Output format

For each region, `print_data` prints six lines:

1. Region name
2. Total region population
3. Largest country name
4. Largest country population
5. Smallest country name
6. Smallest country population

## Project structure

- `population/parsers.py` — HTML parsers (`WikipediaParser`, `StatisticsTimesParser`, `WorldometersParser`)
- `population/repository.py` — PostgreSQL access and aggregation query
- `population/service.py` — `get_data` / `print_data` orchestration
- `population/downloader.py` — HTTP download layer
- `population/config.py` — environment configuration
