from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

from BaseClasses import Item, ItemClassification

from .data import DAYS, PASSES, PICHU_BROS_DISC, PROGRESSIVE_DAY, PROGRAMS, channel_item

if TYPE_CHECKING:
    from .world import PokemonChannelWorld

BASE_ID = 7_041_000


class PokemonChannelItem(Item):
    game = "Pokemon Channel"


class ItemKind(Enum):
    DAY = 0
    PASS = 1
    DISC = 2
    CHANNEL = 3
    FILLER = 4


class ItemData(NamedTuple):
    id: int
    kind: ItemKind
    classification: ItemClassification


FILLER_ITEMS = ("10 Poke Points", "50 Poke Points", "Room Decoration")

_ordered: list[tuple[str, ItemKind, ItemClassification]] = [
    (PROGRESSIVE_DAY, ItemKind.DAY, ItemClassification.progression),
    *((name, ItemKind.PASS, ItemClassification.progression) for name in PASSES),
    (PICHU_BROS_DISC, ItemKind.DISC, ItemClassification.progression),
    *((channel_item(p.name), ItemKind.CHANNEL, ItemClassification.progression) for p in PROGRAMS),
    ("10 Poke Points", ItemKind.FILLER, ItemClassification.filler),
    ("50 Poke Points", ItemKind.FILLER, ItemClassification.filler),
    ("Room Decoration", ItemKind.FILLER, ItemClassification.filler),
]

# IDs are fixed by list position, so only ever append to _ordered.
ITEM_TABLE: dict[str, ItemData] = {
    name: ItemData(BASE_ID + i, kind, classification) for i, (name, kind, classification) in enumerate(_ordered)
}
ITEM_NAME_TO_ID = {name: data.id for name, data in ITEM_TABLE.items()}
ITEM_ID_TO_NAME = {data.id: name for name, data in ITEM_TABLE.items()}

ITEM_NAME_GROUPS = {
    "Bus Passes": set(PASSES),
    "Channels": {channel_item(p.name) for p in PROGRAMS},
}


def create_item(world: "PokemonChannelWorld", name: str) -> PokemonChannelItem:
    return PokemonChannelItem(name, ITEM_TABLE[name].classification, ITEM_NAME_TO_ID[name], world.player)


def create_all_items(world: "PokemonChannelWorld") -> None:
    pool: list[str] = [PROGRESSIVE_DAY] * (DAYS - 1)
    pool += [p for p in PASSES if p != world.starting_pass]
    pool.append(PICHU_BROS_DISC)
    if world.options.channel_shuffle:
        pool += [channel_item(p.name) for p in PROGRAMS if p.name not in world.always_open_channels]

    unfilled = len(world.multiworld.get_unfilled_locations(world.player))
    if len(pool) > unfilled:
        raise RuntimeError(f"Pokemon Channel: {len(pool)} required items but only {unfilled} locations.")
    pool += [world.get_filler_item_name() for _ in range(unfilled - len(pool))]

    world.multiworld.itempool += [create_item(world, name) for name in pool]


def get_random_filler_item_name(world: "PokemonChannelWorld") -> str:
    return world.random.choice(FILLER_ITEMS)
