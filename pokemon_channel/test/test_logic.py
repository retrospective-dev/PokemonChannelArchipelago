from . import PokemonChannelTestBase


class TestDefault(PokemonChannelTestBase):
    def test_days_gate_programs(self) -> None:
        self.assertTrue(self.can_reach_location("Watch PNF"))
        self.assertFalse(self.can_reach_location("Watch Mareep Farm"))
        self.collect_by_name(["Progressive Day"] * 3)
        self.assertTrue(self.can_reach_location("Watch Mareep Farm"))

    def test_passes_gate_regions(self) -> None:
        self.assertFalse(self.can_reach_location("Visit Mt. Snowfall"))
        self.collect_by_name("Snowfall Pass")
        self.assertTrue(self.can_reach_location("Visit Mt. Snowfall"))

    def test_part_five_needs_disc(self) -> None:
        self.collect_by_name(["Progressive Day"] * 5)
        self.assertFalse(self.can_reach_location("Pichu Bros. in Party Panic Part 5"))
        self.collect_by_name("Pichu Bros. Disc")
        self.assertTrue(self.can_reach_location("Pichu Bros. in Party Panic Part 5"))


class TestChannelShuffle(PokemonChannelTestBase):
    options = {"channel_shuffle": True, "starting_pass": "any"}

    def test_channel_items_gate_programs(self) -> None:
        self.assertTrue(self.can_reach_location("Watch Professor Oak's Report"))
        self.assertFalse(self.can_reach_location("Watch PNF"))
        self.collect_by_name("Channel: PNF")
        self.assertTrue(self.can_reach_location("Watch PNF"))


class TestNiceCardGoal(PokemonChannelTestBase):
    options = {"goal": "nice_cards", "nice_card_goal": 110, "nice_card_checks": 110, "pokemon_mini_checks": False}


class TestMinimal(PokemonChannelTestBase):
    options = {"nice_card_checks": 0, "pokemon_mini_checks": False, "channel_shuffle": True}
