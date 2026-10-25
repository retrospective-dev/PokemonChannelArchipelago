# Pokemon Channel Archipelago

An [Archipelago](https://archipelago.gg) world for **Pokemon Channel** (GameCube, 2003).

The six-day calendar, the bus passes, the Pichu Bros. part 5 disc and (optionally) the TV channels themselves are
shuffled into the multiworld. Watching programs, finishing days, visiting the outdoor regions, playing Pokemon mini
games and reaching Nice Card totals send checks.

> **Status: early.** Seeds generate and the client connects to Dolphin, but the game's memory hasn't been mapped
> yet, so checks are sent by hand with `/check` (honor system). See [Contributing](#contributing).

## Install

1. Get Archipelago 0.6.7 or newer.
2. Download `pokemon_channel.apworld` from [Releases](../../releases) and
   double-click it, or drop it in `Archipelago/custom_worlds`.
3. In the Archipelago Launcher, use **Generate Template Options** to get `Pokemon Channel.yaml`.

To build it yourself: `zip -r pokemon_channel.apworld pokemon_channel -x "*/__pycache__/*"`

## Items

| Item | Count | What it does |
| --- | --- | --- |
| Progressive Day | 5 | Lets you go to bed and move one day forward |
| Viridian Pass / Cobalt Pass / Snowfall Pass | 1 each | Lets you take the bus to that region |
| Pichu Bros. Disc | 1 | Lets you watch Pichu Bros. in Party Panic part 5 |
| Channel: *program* | 1 each | Channel Shuffle only: lets you watch that program |
| Poke Points, Room Decoration | filler | |

## Locations

- Finish Day 1-5
- Watch each program for the first time (13 programs, from PNF and Shop 'n Squirtle on day 1 to Mareep Farm on day 4)
- Pichu Bros. in Party Panic Parts 1-5
- Win the Quiz Wobbuffet Present Quiz; finish a painting in Smeargle's Art Study
- Visit Viridian Forest, Cobalt Coast and Mt. Snowfall
- Play each Pokemon mini game (optional)
- Nice Card totals, every 1-10 cards up to all 110 (optional)
- Post-game repeats: watch each program, visit each region and win the Present Quiz on 2-10 different days (optional)

Location count ranges from 28 (Short preset) to 277 (Long preset), so it can keep pace with big games in the
same multiworld.

## Options

| Option | Default | |
| --- | --- | --- |
| `goal` | `finish_story` | `finish_story` (day 6 ending) or `nice_cards` |
| `nice_card_goal` | 60 | Nice Cards needed for the `nice_cards` goal |
| `nice_card_checks` | 60 | Highest Nice Card count that sends a check (0 = off) |
| `nice_card_interval` | 5 | A Nice Card check every this many cards (1 = every card) |
| `repeat_checks` | 1 | Post-game "on N days" checks up to this many days (1 = off, each step adds 15 checks) |
| `channel_shuffle` | off | Lock every program except Professor Oak's Report behind an item |
| `pokemon_mini_checks` | on | Checks for playing each Pokemon mini game |
| `starting_pass` | `none` | Start with a bus pass: `viridian`, `cobalt`, `snowfall` or `any` |

### Presets

- **Short:** about 28 checks, a quick story run.
- **Long (for big multiworlds):** 277 checks. Every Nice Card, repeats up to 10 days, Channel Shuffle on, goal is
  all 110 cards. Use this next to long games like Kingdom Hearts 2 or Sekiro.

```yaml
name: YourName
game: Pokemon Channel
Pokemon Channel:
  goal: nice_cards
  nice_card_goal: 110
  nice_card_checks: 110
  nice_card_interval: 1
  repeat_checks: 10
  channel_shuffle: true
  pokemon_mini_checks: true
  starting_pass: any
```

## Playing

1. Start a new save of Pokemon Channel in Dolphin (GPAE01, GPAP01 or GPAJ01).
2. Open **Pokemon Channel Client** from the Launcher and connect.
3. Only go to bed when you have the next Progressive Day, only take the bus with the pass, and with Channel Shuffle
   only watch channels you've received.
4. Once you have all 5 Progressive Days and have seen the day 6 ending, you're in the post-game: sleep as much as you
   like. Repeat checks and Nice Card totals above 30 all live here.
5. Client commands:
   - `/check <location>`: send a check (part of the name is enough)
   - `/todo`: list what's left
   - `/goal`: send your win
   - `/dolphin`: show the Dolphin connection status

## Contributing

- **Memory map:** `pokemon_channel/ram.py` lists the addresses the client needs (current day, Nice Card count,
  per-location save flags, day 6 ending flag). Once they're filled in, the client sends checks on its own.
- **Game data:** program air days, the Pokemon mini list and the Nice Card difficulty curve live in
  `pokemon_channel/data.py`. Corrections are welcome.
- **Tests:** copy `pokemon_channel` into `Archipelago/worlds/` and run
  `python -m pytest worlds/pokemon_channel/test`.
