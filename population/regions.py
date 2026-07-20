from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict

REGIONS_FILE = Path(__file__).with_name("country_regions.json")

WORLDOMETERS_ALIASES: Dict[str, str] = {
    "czech republic": "Czechia",
    "cote d'ivoire": "Ivory Coast",
    "côte d'ivoire": "Ivory Coast",
    "democratic republic of the congo": "DR Congo",
    "republic of the congo": "Congo",
    "state of palestine": "Palestine",
    "hong kong": "Hong Kong",
    "macao": "Macao",
    "macau": "Macao",
    "reunion": "Réunion",
    "sao tome & principe": "São Tomé and Príncipe",
    "st. vincent & grenadines": "St. Vincent & Grenadines",
    "turks and caicos": "Turks and Caicos Islands",
    "u.s. virgin islands": "U.S. Virgin Islands",
    "british virgin islands": "British Virgin Islands",
    "caribbean netherlands": "Caribbean Netherlands",
    "saint barthelemy": "Saint Barthélemy",
    "wallis & futuna": "Wallis and Futuna",
    "saint pierre & miquelon": "Saint Pierre and Miquelon",
    "holy see": "Vatican City",
    "curacao": "Curaçao",
    "faeroe islands": "Faroe Islands",
    "falkland islands": "Falkland Islands",
    "micronesia": "Federated States of Micronesia",
    "saint martin": "Saint Martin",
    "saint helena": "Saint Helena",
}


def normalize_country_name(name: str) -> str:
    cleaned = name.replace("\xa0", " ")
    cleaned = re.sub(r"\s*\[[^\]]+\]", "", cleaned)
    cleaned = re.sub(r"\s*\([^)]*\)", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip().lower()


def _resolve_region(raw_regions: Dict[str, str], canonical: str) -> str | None:
    target = normalize_country_name(canonical)
    for country_name, region in raw_regions.items():
        if normalize_country_name(country_name) == target:
            return region
    return None


@lru_cache(maxsize=1)
def load_region_lookup() -> Dict[str, str]:
    with REGIONS_FILE.open(encoding="utf-8") as file:
        raw_regions: Dict[str, str] = json.load(file)

    lookup: Dict[str, str] = {}
    for country_name, region in raw_regions.items():
        lookup[normalize_country_name(country_name)] = region

    for alias, canonical in WORLDOMETERS_ALIASES.items():
        region = _resolve_region(raw_regions, canonical)
        if region is not None:
            lookup[alias] = region

    return lookup


def lookup_region(country_name: str) -> str | None:
    return load_region_lookup().get(normalize_country_name(country_name))
