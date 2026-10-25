from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, Optional

from BaseClasses import CollectionState, Location, Region

from .data import (
    DAYS,
    MAX_REPEAT,
    NICE_CARD_MILESTONE_STEP,
    NICE_CARD_TOTAL,
    OUTDOOR_REGIONS,
    PASSES,
    PICHU_BROS_DISC,
    PICHU_BROS_PARTS,
    POKEMON_MINI_GAMES,
    PROGRAMS,
    PROGRESSIVE_DAY,
    REPEATABLE_PROGRAMS,
    channel_item,
)

if TYPE_CHECKING:
    from .world import PokemonChannelWorld

BASE_ID = 7_041_000
HOUSE = "Pikachu's House"
GOAL_EVENT = "Day 6 Ending"
VICTORY = "Victory"


class PokemonChannelLocation(Location):
    game = "Pokemon Channel"


class LocationKind(Enum):
    DAY_END = 0
    PROGRAM = 1
    PICHU_BROS = 2
    EXTRA = 3
    VISIT = 4
    MINI = 5
    NICE_CARDS = 6
    REPEAT = 7


class LocationData(NamedTuple):
    id: int
    kind: LocationKind
    region: str
    day: int  # first day the location can be done on
    program: Optional[str] = None  # channel that has to be unlocked
    item: Optional[str] = None  # any other item that is needed
    cards: int = 0  # Nice Card milestone
    repeat: int = 0  # number of different days, for repeat checks


# Only this many cards are expected during the story. Anything higher is post-game, where the player can
# sleep freely, so a big milestone can never hold the Progressive Day needed to reach it.
STORY_NICE_CARDS = 30


def _nice_card_day(cards: int) -> int:
    if cards > STORY_NICE_CARDS:
        return DAYS
    return 1 + (cards * (DAYS - 2)) // STORY_NICE_CARDS


def _nice_card_passes(cards: int) -> int:
    return (cards * len(PASSES)) // NICE_CARD_TOTAL


_ordered: list[tuple[str, LocationKind, str, int, Optional[str], Optional[str], int]] = [
    *((f"Finish Day {d}", LocationKind.DAY_END, HOUSE, d, None, None, 0) for d in range(1, DAYS)),
    *((f"Watch {p.name}", LocationKind.PROGRAM, HOUSE, p.first_day, p.name, None, 0) for p in PROGRAMS),
    *(
        (
            f"Pichu Bros. in Party Panic Part {n}",
            LocationKind.PICHU_BROS,
            HOUSE,
            n,
            "Pichu Bros. in Party Panic",
            PICHU_BROS_DISC if n == PICHU_BROS_PARTS else None,
            0,
        )
        for n in range(1, PICHU_BROS_PARTS + 1)
    ),
    ("Quiz Wobbuffet: Win the Present Quiz", LocationKind.EXTRA, HOUSE, 1, "Quiz Wobbuffet", None, 0),
    ("Smeargle's Art Study: Finish a Painting", LocationKind.EXTRA, HOUSE, 2, "Smeargle's Art Study", None, 0),
    *((f"Visit {r.name}", LocationKind.VISIT, r.name, 1, None, None, 0) for r in OUTDOOR_REGIONS),
    *((f"Play {g}", LocationKind.MINI, HOUSE, 1, "Shop 'n Squirtle", None, 0) for g in POKEMON_MINI_GAMES),
    *(
        (f"Collect {c} Nice Cards", LocationKind.NICE_CARDS, HOUSE, _nice_card_day(c), None, None, c)
        for c in range(NICE_CARD_MILESTONE_STEP, NICE_CARD_TOTAL + 1, NICE_CARD_MILESTONE_STEP)
    ),
]

# Added in 0.2.0: Nice Cards between the milestones of 5, and the repeat checks.
_ordered += [
    (f"Collect {c} Nice Cards", LocationKind.NICE_CARDS, HOUSE, _nice_card_day(c), None, None, c)
    for c in range(1, NICE_CARD_TOTAL + 1)
    if c % NICE_CARD_MILESTONE_STEP
]
_repeats: list[tuple[str, str, Optional[str], int]] = [
    *((f"Watch {p.name} on {k} Days", HOUSE, p.name, k) for p in REPEATABLE_PROGRAMS for k in range(2, MAX_REPEAT + 1)),
    *((f"Visit {r.name} on {k} Days", r.name, None, k) for r in OUTDOOR_REGIONS for k in range(2, MAX_REPEAT + 1)),
    *(
        (f"Quiz Wobbuffet: Win the Present Quiz {k} Times", HOUSE, "Quiz Wobbuffet", k)
        for k in range(2, MAX_REPEAT + 1)
    ),
]

# IDs are fixed by list position, so only ever append to _ordered and _repeats.
LOCATION_TABLE: dict[str, LocationData] = {
    name: LocationData(BASE_ID + i, kind, region, day, program, item, cards)
    for i, (name, kind, region, day, program, item, cards) in enumerate(_ordered)
}
LOCATION_TABLE.update(
    {
        name: LocationData(BASE_ID + len(_ordered) + i, LocationKind.REPEAT, region, DAYS, program, repeat=k)
        for i, (name, region, program, k) in enumerate(_repeats)
    }
)
LOCATION_NAME_TO_ID = {name: data.id for name, data in LOCATION_TABLE.items()}

LOCATION_NAME_GROUPS = {
    "Programs": {n for n, d in LOCATION_TABLE.items() if d.kind == LocationKind.PROGRAM},
    "Pichu Bros.": {n for n, d in LOCATION_TABLE.items() if d.kind == LocationKind.PICHU_BROS},
    "Outdoors": {n for n, d in LOCATION_TABLE.items() if d.kind == LocationKind.VISIT},
    "Pokemon mini": {n for n, d in LOCATION_TABLE.items() if d.kind == LocationKind.MINI},
    "Nice Cards": {n for n, d in LOCATION_TABLE.items() if d.kind == LocationKind.NICE_CARDS},
    "Repeats": {n for n, d in LOCATION_TABLE.items() if d.kind == LocationKind.REPEAT},
}


def _is_enabled(world: "PokemonChannelWorld", data: LocationData) -> bool:
    if data.kind == LocationKind.MINI:
        return bool(world.options.pokemon_mini_checks)
    if data.kind == LocationKind.NICE_CARDS:
        return data.cards <= world.options.nice_card_checks and data.cards % world.options.nice_card_interval == 0
    if data.kind == LocationKind.REPEAT:
        return data.repeat <= world.options.repeat_checks
    return True


def _rule(world: "PokemonChannelWorld", data: LocationData) -> Callable[[CollectionState], bool]:
    player = world.player
    days_needed = data.day - 1
    items: list[str] = []
    if data.item:
        items.append(data.item)
    if data.program and world.options.channel_shuffle and data.program not in world.always_open_channels:
        items.append(channel_item(data.program))
    passes_needed = _nice_card_passes(data.cards) if data.kind == LocationKind.NICE_CARDS else 0

    def rule(state: CollectionState) -> bool:
        return (
            state.has(PROGRESSIVE_DAY, player, days_needed)
            and state.has_all(items, player)
            and state.has_from_list_unique(PASSES, player, passes_needed)
        )

    return rule


def create_regions_and_locations(world: "PokemonChannelWorld") -> None:
    player = world.player
    house = Region(HOUSE, player, world.multiworld)
    regions = {HOUSE: house}
    for outdoor in OUTDOOR_REGIONS:
        region = Region(outdoor.name, player, world.multiworld)
        regions[outdoor.name] = region
        house.connect(region, f"Bus to {outdoor.name}", lambda state, p=outdoor.bus_pass: state.has(p, player))
    world.multiworld.regions += regions.values()

    for name, data in LOCATION_TABLE.items():
        if not _is_enabled(world, data):
            continue
        location = PokemonChannelLocation(player, name, data.id, regions[data.region])
        location.access_rule = _rule(world, data)
        regions[data.region].locations.append(location)

    goal = PokemonChannelLocation(player, GOAL_EVENT, None, house)
    if world.options.goal == world.options.goal.option_nice_cards:
        cards = world.options.nice_card_goal.value
        goal_data = LocationData(0, LocationKind.NICE_CARDS, HOUSE, _nice_card_day(cards), cards=cards)
    else:
        goal_data = LocationData(0, LocationKind.DAY_END, HOUSE, DAYS)
    goal.access_rule = _rule(world, goal_data)
    goal.place_locked_item(world.create_event(VICTORY))
    house.locations.append(goal)
    world.multiworld.completion_condition[player] = lambda state: state.has(VICTORY, player)
