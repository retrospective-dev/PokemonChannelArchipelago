from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld

from .options import option_presets


class PokemonChannelWebWorld(WebWorld):
    game = "Pokemon Channel"
    theme = "grassFlowers"
    options_presets = option_presets

    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up Pokemon Channel for Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["leslalilulelo"],
        )
    ]
