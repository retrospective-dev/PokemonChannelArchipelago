from collections.abc import Mapping
from typing import Any

from BaseClasses import ItemClassification
from worlds.AutoWorld import World

from . import items, locations
from .data import OUTDOOR_REGIONS, PASSES
from .options import PokemonChannelOptions, StartingPass
from .web_world import PokemonChannelWebWorld


class PokemonChannelWorld(World):
    """
    Pokemon Channel is a 2003 GameCube game where you watch TV with Pikachu. Over six days new programs
    start airing, Shop 'n Squirtle sells bus passes to the great outdoors, and there are Nice Cards to collect.
    """

    game = "Pokemon Channel"
    web = PokemonChannelWebWorld()
    options_dataclass = PokemonChannelOptions
    options: PokemonChannelOptions

    location_name_to_id = locations.LOCATION_NAME_TO_ID
    item_name_to_id = items.ITEM_NAME_TO_ID
    item_name_groups = items.ITEM_NAME_GROUPS
    location_name_groups = locations.LOCATION_NAME_GROUPS
    origin_region_name = locations.HOUSE

    # The save channel never gets locked: without it the player could not save.
    always_open_channels = frozenset({"Professor Oak's Report"})

    starting_pass: str | None

    def generate_early(self) -> None:
        choice = self.options.starting_pass.value
        if choice == StartingPass.option_none:
            self.starting_pass = None
        elif choice == StartingPass.option_any:
            self.starting_pass = self.random.choice(PASSES)
        else:
            self.starting_pass = OUTDOOR_REGIONS[choice - 1].bus_pass
        if self.starting_pass:
            self.multiworld.push_precollected(self.create_item(self.starting_pass))

    def create_regions(self) -> None:
        locations.create_regions_and_locations(self)

    def create_items(self) -> None:
        items.create_all_items(self)

    def create_item(self, name: str) -> items.PokemonChannelItem:
        return items.create_item(self, name)

    def create_event(self, name: str) -> items.PokemonChannelItem:
        return items.PokemonChannelItem(name, ItemClassification.progression, None, self.player)

    def get_filler_item_name(self) -> str:
        return items.get_random_filler_item_name(self)

    def fill_slot_data(self) -> Mapping[str, Any]:
        return self.options.as_dict(
            "goal",
            "nice_card_goal",
            "nice_card_checks",
            "nice_card_interval",
            "repeat_checks",
            "channel_shuffle",
            "pokemon_mini_checks",
        )
