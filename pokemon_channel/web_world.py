from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld


class PokemonChannelWebWorld(WebWorld):
    game = "Pokemon Channel"
    theme = "grassFlowers"

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
