"""
Dolphin memory map for Pokemon Channel.

None of these have been found yet. Each one needs to be found with Dolphin Memory Engine or
Dolphin's debugger against a known game revision. Until an address is filled in, the client
leaves the matching locations to the /check command.
"""

from typing import Optional

# First six bytes of GameCube memory hold the game ID.
GAME_IDS = {
    b"GPAE01": "NTSC-U",
    b"GPAP01": "PAL",
    b"GPAJ01": "NTSC-J",
}

# Current in-game day, 1-6. One byte.
CURRENT_DAY: Optional[int] = None

# Number of Nice Cards owned. One byte.
NICE_CARD_COUNT: Optional[int] = None

# Set when the day 6 ending has played.
STORY_COMPLETE_FLAG: Optional[tuple[int, int]] = None  # (address, bit)

# Location name -> (address, bit) of the save flag that marks it done.
LOCATION_FLAGS: dict[str, tuple[int, int]] = {}
