"""Parser for coordinates.txt.

The file groups sights into sections:

    [Section 1 -- Пирогова]

    54.836009, 83.10096 ДУ
    54.83478, 83.099032 больница
    ...

Sections 1-3 are the three sectors students route through during the main
quest (in the order they were told IRL, e.g. "2-1-3"). Section 4 is the
bonus round offered after the main route is finished ("Еще места для самых
смелых").
"""

import re
from dataclasses import dataclass

SECTION_RE = re.compile(r"^\[Section\s+(\d+)\s*(?:--\s*(.*))?\]$")
SIGHT_RE = re.compile(r"^(-?\d+(?:[.,]\d+)?)\s*,\s*(-?\d+(?:[.,]\d+)?)\s+(.+)$")


@dataclass(frozen=True)
class Sight:
    lat: float
    lon: float
    name: str


def parse_coordinates(path: str) -> dict[int, list[Sight]]:
    """Read coordinates.txt and return {sector_number: [Sight, ...]}."""
    sectors: dict[int, list[Sight]] = {}
    current_sector: int | None = None

    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            section_match = SECTION_RE.match(line)
            if section_match:
                current_sector = int(section_match.group(1))
                sectors.setdefault(current_sector, [])
                continue

            sight_match = SIGHT_RE.match(line)
            if sight_match and current_sector is not None:
                lat = float(sight_match.group(1).replace(",", "."))
                lon = float(sight_match.group(2).replace(",", "."))
                name = sight_match.group(3).strip()
                sectors[current_sector].append(Sight(lat=lat, lon=lon, name=name))

    return sectors
