"""
Find where Pokemon Channel keeps the values the Archipelago client needs, by comparing snapshots.

A snapshot is a copy of the game's RAM (MEM1) or of a save file, labelled with what you know about
the game at that moment: the day, how many Nice Cards you have, whether you've watched PNF yet...
The script reports every address whose contents match the labels in every snapshot. The more
snapshots, and the more the labels differ between them, the shorter the list.

    pip install numpy dolphin-memory-engine

    # easiest: start this, play normally (sleep at least once, pick up a Nice Card), then press Ctrl+C.
    # It asks for the day and your Nice Card count at the start and at the end, and that's all.
    python find_addresses.py record

    # or take labelled RAM snapshots by hand as you play
    python find_addresses.py capture day1     --day 1 --cards 0  --flag watched_pnf=false
    python find_addresses.py capture day1_pnf --day 1 --cards 0  --flag watched_pnf=true
    python find_addresses.py capture day2     --day 2 --cards 4  --flag watched_pnf=true
    python find_addresses.py analyze

    # Comparing save files (.gci, or GameShark .sav) is supported, but Pokemon Channel scrambles its saves,
    # so for this game the script stops and points you to 'capture'. Kept for games that don't.
    python find_addresses.py add new.gci       --day 1 --cards 0
    python find_addresses.py add day3.gci      --day 3 --cards 17
    python find_addresses.py add completed.gci --day 6 --cards 110
    python find_addresses.py analyze
    # then, with the game loaded from any save, find where that save sits in RAM
    python find_addresses.py locate completed.gci

Labels:
    --day N, --points N, --value name=N   numbers (searched as 8, 16 and 32 bit, big-endian)
    --cards N                             Nice Cards: searched as a plain count and as one bit per card
    --flag name=true|false                on/off things: searched as single bits
"""

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np

MEM1_BASE = 0x80000000
MEM1_SIZE = 0x01800000
GCI_HEADER = 0x40
GAME_IDS = (b"GPAE01", b"GPAP01", b"GPAJ01")
CARD_FIELD_BYTES = (14, 15, 16)  # 110 cards fit in 14 bytes; allow some padding
MAX_PRINTED = 20

ROOT = Path(__file__).resolve().parent / "snapshots"
MANIFEST = ROOT / "manifest.json"

# Pokemon Channel XORs its save data with this 35-byte key, restarting it at points that depend on the
# contents, so positions in a save don't line up between saves or with RAM.
SAVE_SCRAMBLE_KEY = bytes.fromhex("c36dcf8adc4d516f9e76a4454684c90ecd4785782fe971a3fdf6625624163efab09668")

POPCOUNT = np.array([bin(i).count("1") for i in range(256)], dtype=np.int32)


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {"kind": None, "snapshots": []}


def save_manifest(manifest: dict) -> None:
    ROOT.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2))


def labels_from_args(args: argparse.Namespace) -> dict:
    labels: dict = {"values": {}, "flags": {}}
    if args.day is not None:
        labels["values"]["day"] = args.day
    if args.points is not None:
        labels["values"]["points"] = args.points
    if args.cards is not None:
        labels["cards"] = args.cards
    for item in args.value or []:
        name, _, number = item.partition("=")
        labels["values"][name] = int(number, 0)
    for item in args.flag or []:
        name, _, state = item.partition("=")
        if state.lower() not in ("true", "false"):
            raise SystemExit(f"--flag {item}: use name=true or name=false")
        labels["flags"][name] = state.lower() == "true"
    return labels


def add_snapshot(manifest: dict, kind: str, name: str, file: str, labels: dict) -> None:
    if manifest["kind"] not in (None, kind):
        raise SystemExit(f"This snapshot set holds {manifest['kind']} snapshots; don't mix in {kind} ones. "
                         f"Move {ROOT} away to start a new set.")
    manifest["kind"] = kind
    manifest["snapshots"] = [s for s in manifest["snapshots"] if s["name"] != name]
    manifest["snapshots"].append({"name": name, "file": file, **labels})
    save_manifest(manifest)
    print(f"Saved snapshot '{name}' ({len(manifest['snapshots'])} in set).")


def hook_dolphin():
    import dolphin_memory_engine as dme

    dme.hook()
    if not dme.is_hooked():
        raise SystemExit("Couldn't hook Dolphin. Is the game running?")
    game_id = dme.read_bytes(MEM1_BASE, 6)
    if game_id not in GAME_IDS:
        raise SystemExit(f"Dolphin is running {game_id!r}, not Pokemon Channel.")
    return dme


def read_mem1(dme=None) -> bytes:
    dme = dme or hook_dolphin()
    chunk = 0x100000
    return b"".join(dme.read_bytes(MEM1_BASE + off, chunk) for off in range(0, MEM1_SIZE, chunk))


def read_save(path: Path) -> bytes:
    data = path.read_bytes()
    if data.startswith(b"DATELGC_SAVE"):  # GameShark / Action Replay .sav: 0x80-byte header in front of the GCI
        data = data[0x80:]
    if path.suffix.lower() in (".gci", ".sav"):
        if data[:6] not in GAME_IDS:
            print(f"Warning: {path.name} doesn't look like a Pokemon Channel save ({data[:6]!r}).")
        data = data[GCI_HEADER:]
    return data


def cmd_capture(args: argparse.Namespace) -> None:
    manifest = load_manifest()
    ROOT.mkdir(exist_ok=True)
    file = f"{args.name}.bin"
    (ROOT / file).write_bytes(read_mem1())
    add_snapshot(manifest, "ram", args.name, file, labels_from_args(args))


def cmd_add(args: argparse.Namespace) -> None:
    manifest = load_manifest()
    path = Path(args.file).resolve()
    if not path.is_file():
        raise SystemExit(f"{path} doesn't exist.")
    kind = "ram" if args.ram else "save"
    add_snapshot(manifest, kind, args.name or path.stem, str(path), labels_from_args(args))


def load_arrays(manifest: dict) -> list[np.ndarray]:
    arrays = []
    for snap in manifest["snapshots"]:
        path = Path(snap["file"])
        if not path.is_absolute():
            path = ROOT / path
        is_save = manifest["kind"] == "save" and path.suffix.lower() in (".gci", ".sav")
        data = read_save(path) if is_save else path.read_bytes()
        arrays.append(np.frombuffer(data, dtype=np.uint8))
    size = min(len(a) for a in arrays)
    if any(len(a) != size for a in arrays):
        print(f"Note: snapshots differ in size, comparing the first {size:#x} bytes.")
    return [a[:size] for a in arrays]


def words(a: np.ndarray, width: int) -> np.ndarray:
    """Big-endian value starting at every byte offset."""
    value = np.zeros(len(a) - width + 1, dtype=np.uint64)
    for i in range(width):
        value = (value << np.uint64(8)) | a[i : len(a) - width + 1 + i].astype(np.uint64)
    return value


def show(title: str, hits: list[str]) -> None:
    print(f"\n{title}: {len(hits) if hits else 'no'} candidate(s)")
    for line in hits[:MAX_PRINTED]:
        print("   ", line)
    if len(hits) > MAX_PRINTED:
        print(f"    ... and {len(hits) - MAX_PRINTED} more: take another snapshot with different values.")


def find_value(arrays: list[np.ndarray], targets: list[int], base: int) -> list[str]:
    hits = []
    for width in (1, 2, 4):
        stacks = [words(a, width) for a in arrays]
        for shift, note in ((0, ""), (-1, " (counts from 0)")):
            m = np.ones(len(stacks[0]), dtype=bool)
            for values, target in zip(stacks, targets):
                if target + shift < 0:
                    m[:] = False
                    break
                m &= values == np.uint64(target + shift)
            for off in np.flatnonzero(m):
                aligned = "" if off % width else " aligned"
                hits.append((off % width != 0, f"{base + off:#010x}  {width * 8}-bit{aligned}{note}"))
    return [line for _, line in sorted(hits, key=lambda h: h[0])]


def find_cards(arrays: list[np.ndarray], counts: list[int], base: int) -> list[str]:
    hits = [f"{line}  (plain count)" for line in find_value(arrays, counts, base)]
    cumulative = [np.concatenate(([0], np.cumsum(POPCOUNT[a]))) for a in arrays]
    for length in CARD_FIELD_BYTES:
        m = np.ones(len(arrays[0]) - length + 1, dtype=bool)
        for cum, count in zip(cumulative, counts):
            m &= (cum[length:] - cum[:-length]) == count
        # Cards are never lost: a bit set in an earlier snapshot (fewer cards) stays set in later ones.
        order = np.argsort(counts)
        for earlier, later in zip(order, order[1:]):
            gained = arrays[earlier] & ~arrays[later]  # bits that disappeared
            lost = np.concatenate(([0], np.cumsum(gained != 0)))
            m &= (lost[length:] - lost[:-length]) == 0
        for off in np.flatnonzero(m):
            hits.append(f"{base + off:#010x}  {length} bytes, one bit per card")
    return hits


def find_flag(arrays: list[np.ndarray], states: list[bool], base: int) -> list[str]:
    on = np.full(len(arrays[0]), 0xFF, dtype=np.uint8)
    for a, state in zip(arrays, states):
        on &= a if state else ~a
    hits = []
    for off in np.flatnonzero(on):
        for bit in range(8):
            if on[off] >> bit & 1:
                # A real flag usually sits in a byte whose other bits don't move around: list those first.
                others = len({int(a[off]) & ~(1 << bit) for a in arrays})
                quiet = "" if others == 1 else f", {others} other values in this byte"
                hits.append((others, f"{base + off:#010x}  bit {bit} (mask {1 << bit:#04x}){quiet}"))
    return [line for _, line in sorted(hits, key=lambda h: h[0])]


def cmd_analyze(args: argparse.Namespace) -> None:
    manifest = load_manifest()
    snaps = manifest["snapshots"]
    if len(snaps) < 2:
        raise SystemExit("Need at least two snapshots to compare.")
    arrays = load_arrays(manifest)
    if manifest["kind"] == "save" and any(SAVE_SCRAMBLE_KEY in a.tobytes() for a in arrays):
        raise SystemExit("These saves are scrambled (Pokemon Channel XORs its save data with a shifting key), so "
                         "comparing them gives meaningless results. Use RAM snapshots instead: run 'capture' "
                         "with the game running in Dolphin.")
    base = MEM1_BASE if manifest["kind"] == "ram" else 0
    where = "RAM address" if base else "offset in the save (run 'locate' to turn these into RAM addresses)"
    print(f"Comparing {len(snaps)} {manifest['kind']} snapshots; results are {where}.")

    names = sorted({k for s in snaps for k in s.get("values", {})})
    for name in names:
        labelled = [(a, s["values"][name]) for a, s in zip(arrays, snaps) if name in s.get("values", {})]
        if len({v for _, v in labelled}) < 2:
            print(f"\n{name}: skipped, it needs two snapshots with different values.")
            continue
        show(name, find_value([a for a, _ in labelled], [v for _, v in labelled], base))

    labelled = [(a, s["cards"]) for a, s in zip(arrays, snaps) if "cards" in s]
    if len({c for _, c in labelled}) >= 2:
        show("Nice Cards", find_cards([a for a, _ in labelled], [c for _, c in labelled], base))
    elif labelled:
        print("\nNice Cards: skipped, it needs two snapshots with different card counts.")

    flags = sorted({k for s in snaps for k in s.get("flags", {})})
    for name in flags:
        labelled = [(a, s["flags"][name]) for a, s in zip(arrays, snaps) if name in s.get("flags", {})]
        if len({v for _, v in labelled}) < 2:
            print(f"\n{name}: skipped, it needs a snapshot where it's true and one where it's false.")
            continue
        show(f"flag {name}", find_flag([a for a, _ in labelled], [v for _, v in labelled], base))


def cmd_locate(args: argparse.Namespace) -> None:
    save = read_save(Path(args.save))
    if SAVE_SCRAMBLE_KEY in save:
        raise SystemExit("This save is scrambled, so it won't appear as-is in RAM. Use 'capture' instead.")
    ram = Path(args.ram).read_bytes() if args.ram else read_mem1()
    votes: Counter[int] = Counter()
    for off in range(0, len(save) - 32, 16):
        chunk = save[off : off + 32]
        if len(set(chunk)) < 4:  # runs of zeros/FFs match everywhere
            continue
        pos = ram.find(chunk)
        if pos >= 0 and ram.find(chunk, pos + 1) < 0:
            votes[pos - off] += 1
    if not votes:
        raise SystemExit("The save wasn't found in RAM. It may be compressed or checksummed in a way that "
                         "changes it; use RAM snapshots ('capture') instead.")
    delta, count = votes.most_common(1)[0]
    print(f"Save offset 0 is at RAM {MEM1_BASE + delta:#010x} ({count} matching pieces).")
    print(f"RAM address = {MEM1_BASE + delta:#010x} + save offset.")
    print("Check it with a fresh 'capture' after loading a different save: the copy may move.")


def ask_number(question: str, allow_blank: bool = False) -> int | None:
    while True:
        answer = input(question).strip()
        if answer.isdigit():
            return int(answer)
        if allow_blank and not answer:
            return None
        print("Please type a number." + (" Or just press Enter if you don't know." if allow_blank else ""))


def cmd_record(args: argparse.Namespace) -> None:
    dme = hook_dolphin()
    print("Load your save in Dolphin and get to where you can move Pikachu around.")
    start_day = ask_number("What day is it in the game right now? (Enter if you don't know) ", allow_blank=True)
    start_cards = ask_number("How many Nice Cards do you have right now? ")

    first = np.frombuffer(read_mem1(dme), dtype=np.uint8).copy()
    prev = first.copy()
    bad_step = np.zeros(len(first), dtype=bool)  # changed by something other than +1
    cleared = np.zeros(len(first), dtype=np.uint8)  # bits that were ever switched off
    samples = 0
    print("\nRecording. Play normally: sleep at least once and pick up a Nice Card or two.")
    print("Press Ctrl+C when you're done.\n")
    started = time.monotonic()
    try:
        while True:
            time.sleep(args.interval)
            if not dme.is_hooked():
                print("Lost Dolphin. Stopping.")
                break
            cur = np.frombuffer(read_mem1(dme), dtype=np.uint8)
            changed = cur != prev
            bad_step |= changed & (cur != prev + np.uint8(1))
            cleared |= prev & ~cur
            prev = cur.copy()
            samples += 1
            if samples % 20 == 0:
                print(f"  {int(time.monotonic() - started)}s recorded", end="\r")
    except KeyboardInterrupt:
        pass
    last = prev
    print(f"\nStopped after {samples} samples.")
    if start_day is None:
        slept = ask_number("How many times did you sleep? ")
        end_day = None
    else:
        end_day = ask_number("What day is it now? ")
        slept = end_day - start_day
    end_cards = ask_number("How many Nice Cards do you have now? ")

    report: list[str] = []

    def out(line: str = "") -> None:
        print(line)
        report.append(line)

    if slept > 0:
        hits = []
        if start_day is None:
            m = ~bad_step & (last.astype(np.int16) - first == slept)
            hits += [f"{MEM1_BASE + off:#010x}  8-bit, now {last[off]}" for off in np.flatnonzero(m)]
        else:
            for shift, note in ((0, ""), (1, " (counts from 0)")):
                m = ~bad_step & (first == start_day - shift) & (last == end_day - shift)
                hits += [f"{MEM1_BASE + off:#010x}  8-bit{note}" for off in np.flatnonzero(m)]
        out(f"\nDay: {len(hits) or 'no'} candidate(s)")
        out("\n".join("    " + h for h in hits[:MAX_PRINTED]))
        if len(hits) > MAX_PRINTED:
            out(f"    ... and {len(hits) - MAX_PRINTED} more: record again and sleep a few more times.")
    else:
        out("\nDay: you didn't sleep, so it can't be found from this recording.")

    if end_cards > start_cards:
        hits = []
        m = ~bad_step & (first == start_cards) & (last == end_cards)
        hits += [f"{MEM1_BASE + off:#010x}  8-bit count" for off in np.flatnonzero(m)]
        never_cleared = np.concatenate(([0], np.cumsum(cleared != 0)))
        pop_first = np.concatenate(([0], np.cumsum(POPCOUNT[first])))
        pop_last = np.concatenate(([0], np.cumsum(POPCOUNT[last])))
        for length in CARD_FIELD_BYTES:
            w = ((never_cleared[length:] - never_cleared[:-length]) == 0) \
                & ((pop_first[length:] - pop_first[:-length]) == start_cards) \
                & ((pop_last[length:] - pop_last[:-length]) == end_cards)
            hits += [f"{MEM1_BASE + off:#010x}  {length} bytes, one bit per card" for off in np.flatnonzero(w)]
        out(f"\nNice Cards: {len(hits) or 'no'} candidate(s)")
        out("\n".join("    " + h for h in hits[:MAX_PRINTED]))
        if len(hits) > MAX_PRINTED:
            out(f"    ... and {len(hits) - MAX_PRINTED} more: record again and get a few more cards.")
    elif start_cards >= 110:
        out("\nNice Cards: you already have them all, so there's nothing to watch. Use a save that's missing some.")
    else:
        out("\nNice Cards: you didn't get any, so they can't be found from this recording.")

    ROOT.mkdir(exist_ok=True)
    result = ROOT / "record_result.txt"
    result.write_text("\n".join(report) + "\n")
    print(f"\nSaved to {result}. Send that file over.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def label_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--day", type=int)
        p.add_argument("--cards", type=int)
        p.add_argument("--points", type=int)
        p.add_argument("--value", action="append", metavar="NAME=N")
        p.add_argument("--flag", action="append", metavar="NAME=true|false")

    p = sub.add_parser("record", help="watch Dolphin while you play and find the day and Nice Cards")
    p.add_argument("--interval", type=float, default=0.5, help="seconds between reads (default 0.5)")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("capture", help="snapshot Dolphin's RAM now")
    p.add_argument("name")
    label_args(p)
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("add", help="add a save file (.gci) or a RAM dump as a snapshot")
    p.add_argument("file")
    p.add_argument("--name")
    p.add_argument("--ram", action="store_true", help="the file is a MEM1 dump, not a save")
    label_args(p)
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("analyze", help="list addresses that match every snapshot")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("locate", help="find where a save's data sits in RAM")
    p.add_argument("save")
    p.add_argument("--ram", help="a MEM1 dump to search instead of live Dolphin")
    p.set_defaults(func=cmd_locate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
