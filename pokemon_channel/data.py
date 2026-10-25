"""
Static game data for Pokemon Channel (GameCube, 2003).

The main game runs over six in-game days. New programs start airing as days pass,
bus passes from Shop 'n Squirtle open the three outdoor regions, and Nice Cards are
collected along the way.

In the randomizer, the calendar itself is an item: "Progressive Day" moves you one
day forward, so a day N location needs N - 1 copies of it.
"""

from typing import NamedTuple

DAYS = 6
NICE_CARD_TOTAL = 110

PROGRESSIVE_DAY = "Progressive Day"
VIRIDIAN_PASS = "Viridian Pass"
COBALT_PASS = "Cobalt Pass"
SNOWFALL_PASS = "Snowfall Pass"
PASSES = (VIRIDIAN_PASS, COBALT_PASS, SNOWFALL_PASS)
PICHU_BROS_DISC = "Pichu Bros. Disc"


class Program(NamedTuple):
    name: str
    first_day: int


# (program, day it first airs). Professor Oak's Report is the save channel and is always available.
PROGRAMS: tuple[Program, ...] = (
    Program("Professor Oak's Report", 1),
    Program("PNF", 1),
    Program("Shop 'n Squirtle", 1),
    Program("Smoochum Shape-up", 1),
    Program("Quiz Wobbuffet", 1),
    Program("Pichu Bros. in Party Panic", 1),
    Program("Slowpoke's Weather Report", 2),
    Program("Smeargle's Art Study", 2),
    Program("Eggzamination", 3),
    Program("Chansey's Fortune", 3),
    Program("Mareep Farm", 4),
    Program("Chum Chum Ranking", 4),
    Program("Odd One Out", 4),
)

# Channels that start off locked when channel shuffle is on. The save channel always works.
LOCKABLE_PROGRAMS = tuple(p for p in PROGRAMS if p.name != "Professor Oak's Report")


def channel_item(program: str) -> str:
    return f"Channel: {program}"


class Region(NamedTuple):
    name: str
    bus_pass: str


OUTDOOR_REGIONS: tuple[Region, ...] = (
    Region("Viridian Forest", VIRIDIAN_PASS),
    Region("Cobalt Coast", COBALT_PASS),
    Region("Mt. Snowfall", SNOWFALL_PASS),
)

# Pichu Bros. in Party Panic: parts 1-4 air on days 1-4, part 5 comes on a disc on day 5.
PICHU_BROS_PARTS = 5

# Pokemon mini software available in the international release (via Shop 'n Squirtle).
POKEMON_MINI_GAMES = (
    "Snorlax's Lunch Time",
    "Pokemon Party mini",
    "Pokemon Pinball mini",
    "Pokemon Puzzle Collection",
)

NICE_CARD_MILESTONE_STEP = 5

# Repeat checks ("Watch PNF on 3 Days") go up to this many days. They all count as post-game:
# once every Progressive Day is in, the player can sleep freely, so a late channel or pass
# can never leave one of them out of reach.
MAX_REPEAT = 10
REPEATABLE_PROGRAMS = tuple(
    p for p in PROGRAMS if p.name not in ("Professor Oak's Report", "Pichu Bros. in Party Panic")
)
