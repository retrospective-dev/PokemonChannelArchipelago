# Pokemon Channel

## What does randomization do to this game?

The calendar, the bus passes, the Pichu Bros. part 5 disc and (optionally) the TV channels themselves become
items shuffled into the multiworld. Watching programs, finishing days, visiting the outdoor regions, playing
Pokemon mini games and reaching Nice Card totals send checks.

## What are the items?

- **Progressive Day** (5): each copy lets you move one day forward. Hold off on sleeping until you have one.
- **Viridian Pass / Cobalt Pass / Snowfall Pass**: let you ride the bus to that region.
- **Pichu Bros. Disc**: lets you watch Pichu Bros. in Party Panic part 5.
- **Channel: ...** (Channel Shuffle only): lets you watch that program.
- Filler: Poke Points and room decorations.

## What is the goal?

Either reach the day 6 ending, or collect a set number of Nice Cards.

## How does the game know what I did?

The client hooks into Dolphin, but the game's memory hasn't been mapped yet, so for now this is played on the
honor system: use `/check <location>` when you do something, `/todo` to see what's left and `/goal` when you
finish. Don't use anything the multiworld hasn't sent you yet.
