from . import PokemonChannelTestBase


class TestDefault(PokemonChannelTestBase):
    def test_days_gate_programs(self) -> None:
        self.assertTrue(self.can_reach_location("Watch PNF"))
        self.assertFalse(self.can_reach_location("Watch Mareep Farm"))
        self.collect(self.get_items_by_name("Progressive Day")[:3])
        self.assertTrue(self.can_reach_location("Watch Mareep Farm"))

    def test_passes_gate_regions(self) -> None:
        self.assertFalse(self.can_reach_location("Visit Mt. Snowfall"))
        self.collect_by_name("Snowfall Pass")
        self.assertTrue(self.can_reach_location("Visit Mt. Snowfall"))

    def test_part_five_needs_disc(self) -> None:
        self.collect_by_name("Progressive Day")
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


class TestLong(PokemonChannelTestBase):
    options = {
        "goal": "nice_cards",
        "nice_card_goal": 110,
        "nice_card_checks": 110,
        "nice_card_interval": 1,
        "repeat_checks": 10,
        "channel_shuffle": True,
    }

    def test_location_count(self) -> None:
        # 32 base + 110 Nice Cards + 15 * 9 repeats + the goal event
        self.assertEqual(len(self.multiworld.get_locations(self.player)), 278)

    def test_repeats_are_post_game(self) -> None:
        self.collect_by_name("Channel: PNF")
        days = self.get_items_by_name("Progressive Day")
        self.collect(days[:4])
        self.assertFalse(self.can_reach_location("Watch PNF on 2 Days"))
        self.collect(days[4:])
        self.assertTrue(self.can_reach_location("Watch PNF on 10 Days"))

    def test_repeat_visits_need_pass(self) -> None:
        self.collect_by_name("Progressive Day")
        self.assertFalse(self.can_reach_location("Visit Cobalt Coast on 3 Days"))
        self.collect_by_name("Cobalt Pass")
        self.assertTrue(self.can_reach_location("Visit Cobalt Coast on 3 Days"))


class TestNiceCardsNeverHoldTheirOwnDay(PokemonChannelTestBase):
    options = {"nice_card_checks": 110, "nice_card_interval": 1}

    def test_big_milestones_are_post_game(self) -> None:
        days = self.get_items_by_name("Progressive Day")
        self.collect(days[:4])
        self.collect_by_name(["Viridian Pass", "Cobalt Pass", "Snowfall Pass"])
        self.assertTrue(self.can_reach_location("Collect 30 Nice Cards"))
        self.assertFalse(self.can_reach_location("Collect 31 Nice Cards"))
