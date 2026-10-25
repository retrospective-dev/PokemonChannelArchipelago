from dataclasses import dataclass

from Options import Choice, PerGameCommonOptions, Range, Toggle

from .data import NICE_CARD_TOTAL


class Goal(Choice):
    """
    What you need to do to finish.
    finish_story: reach the end of day 6.
    nice_cards: collect the number of Nice Cards set in Nice Card Goal.
    """

    display_name = "Goal"
    option_finish_story = 0
    option_nice_cards = 1
    default = 0


class NiceCardGoal(Range):
    """How many Nice Cards you need when the goal is nice_cards."""

    display_name = "Nice Card Goal"
    range_start = 5
    range_end = NICE_CARD_TOTAL
    default = 60


class NiceCardChecks(Range):
    """
    The highest Nice Card count that sends checks, one check every 5 cards.
    0 turns Nice Card checks off.
    """

    display_name = "Nice Card Checks"
    range_start = 0
    range_end = NICE_CARD_TOTAL
    default = 60


class NiceCardInterval(Range):
    """
    Send a Nice Card check every this many cards. 1 makes every card a check;
    use it with Nice Card Checks 110 for a long game.
    """

    display_name = "Nice Card Interval"
    range_start = 1
    range_end = 10
    default = 5


class RepeatChecks(Range):
    """
    Extra post-game checks for doing things on more than one day: watching each program,
    visiting each region and winning the Present Quiz on 2, 3, ... up to this many days.
    1 turns them off. Each step adds 15 checks.
    After you have every Progressive Day and have seen day 6, you can sleep as much as you like.
    """

    display_name = "Repeat Checks"
    range_start = 1
    range_end = 10
    default = 1


class ChannelShuffle(Toggle):
    """
    Every program except Professor Oak's Report starts locked and has to be found as an item,
    on top of airing on its usual day.
    """

    display_name = "Channel Shuffle"


class PokemonMiniChecks(Toggle):
    """Playing each Pokemon mini game for the first time sends a check."""

    display_name = "Pokemon mini Checks"
    default = 1


class StartingPass(Choice):
    """Give one bus pass at the start, so day 1 has somewhere to go. "any" picks one of the three."""

    display_name = "Starting Bus Pass"
    option_none = 0
    option_viridian = 1
    option_cobalt = 2
    option_snowfall = 3
    option_any = 4
    default = 0


@dataclass
class PokemonChannelOptions(PerGameCommonOptions):
    goal: Goal
    nice_card_goal: NiceCardGoal
    nice_card_checks: NiceCardChecks
    nice_card_interval: NiceCardInterval
    repeat_checks: RepeatChecks
    channel_shuffle: ChannelShuffle
    pokemon_mini_checks: PokemonMiniChecks
    starting_pass: StartingPass


option_presets = {
    "Long (for big multiworlds)": {
        "goal": "nice_cards",
        "nice_card_goal": 110,
        "nice_card_checks": 110,
        "nice_card_interval": 1,
        "repeat_checks": 10,
        "channel_shuffle": True,
        "pokemon_mini_checks": True,
        "starting_pass": "any",
    },
    "Short": {
        "nice_card_checks": 0,
        "repeat_checks": 1,
        "pokemon_mini_checks": False,
    },
}
