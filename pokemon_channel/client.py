import asyncio
from typing import Any, Optional

import Utils
from CommonClient import ClientCommandProcessor, CommonContext, get_base_parser, gui_enabled, handle_url_arg, logger, server_loop
from NetUtils import ClientStatus

from . import ram
from .locations import LOCATION_NAME_TO_ID, LOCATION_TABLE, LocationKind

try:
    import dolphin_memory_engine as dme
except ImportError:
    dme = None

DOLPHIN_INTERVAL = 0.5


class PokemonChannelCommandProcessor(ClientCommandProcessor):
    def _cmd_dolphin(self) -> None:
        """Show the Dolphin connection status."""
        if isinstance(self.ctx, PokemonChannelContext):
            logger.info(f"Dolphin: {self.ctx.dolphin_status}")

    def _cmd_check(self, *name: str) -> bool:
        """Mark a location as done by name, e.g. /check Watch PNF"""
        if not isinstance(self.ctx, PokemonChannelContext):
            return False
        wanted = " ".join(name).strip().lower()
        matches = [n for n in self.ctx.location_names_in_slot() if wanted and wanted in n.lower()]
        exact = [n for n in matches if n.lower() == wanted]
        if exact:
            matches = exact
        if len(matches) != 1:
            logger.info("No matching location." if not matches else "Matches: " + ", ".join(sorted(matches)))
            return False
        Utils.async_start(self.ctx.send_checks([matches[0]]))
        return True

    def _cmd_goal(self) -> None:
        """Tell the server you reached your goal."""
        if isinstance(self.ctx, PokemonChannelContext):
            Utils.async_start(self.ctx.send_goal())

    def _cmd_todo(self) -> None:
        """List the locations you still have to do."""
        if isinstance(self.ctx, PokemonChannelContext):
            for name in sorted(self.ctx.location_names_in_slot() - self.ctx.checked_names()):
                logger.info(name)


class PokemonChannelContext(CommonContext):
    command_processor = PokemonChannelCommandProcessor
    game = "Pokemon Channel"
    items_handling = 0b111

    def __init__(self, server_address: Optional[str], password: Optional[str]) -> None:
        super().__init__(server_address, password)
        self.dolphin_status = "not connected"
        self.slot_data: dict[str, Any] = {}
        self.goal_sent = False

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict[str, Any]) -> None:
        if cmd == "Connected":
            self.slot_data = args.get("slot_data", {})

    def location_names_in_slot(self) -> set[str]:
        ids = self.server_locations or set(LOCATION_NAME_TO_ID.values())
        return {self.location_names.lookup_in_game(i) for i in ids}

    def checked_names(self) -> set[str]:
        return {self.location_names.lookup_in_game(i) for i in self.checked_locations}

    async def send_checks(self, names: list[str]) -> None:
        ids = [LOCATION_NAME_TO_ID[n] for n in names if LOCATION_NAME_TO_ID[n] in self.missing_locations]
        if ids:
            await self.check_locations(ids)

    async def send_goal(self) -> None:
        if not self.goal_sent and self.slot is not None:
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            self.goal_sent = True
            logger.info("Goal sent!")

    def make_gui(self):
        ui = super().make_gui()
        ui.base_title = "Archipelago Pokemon Channel Client"
        return ui


def _read_flag(flag: tuple[int, int]) -> bool:
    address, bit = flag
    return bool((dme.read_byte(address) >> bit) & 1)


async def _poll_game(ctx: PokemonChannelContext) -> None:
    done = [name for name, flag in ram.LOCATION_FLAGS.items() if _read_flag(flag)]

    if ram.CURRENT_DAY is not None:
        day = dme.read_byte(ram.CURRENT_DAY)
        done += [n for n, d in LOCATION_TABLE.items() if d.kind == LocationKind.DAY_END and d.day < day]

    cards = dme.read_byte(ram.NICE_CARD_COUNT) if ram.NICE_CARD_COUNT is not None else None
    if cards is not None:
        done += [n for n, d in LOCATION_TABLE.items() if d.kind == LocationKind.NICE_CARDS and d.cards <= cards]

    await ctx.send_checks(done)

    goal = ctx.slot_data.get("goal", 0)
    if goal == 0 and ram.STORY_COMPLETE_FLAG is not None and _read_flag(ram.STORY_COMPLETE_FLAG):
        await ctx.send_goal()
    elif goal == 1 and cards is not None and cards >= ctx.slot_data.get("nice_card_goal", 0):
        await ctx.send_goal()


async def dolphin_sync_task(ctx: PokemonChannelContext) -> None:
    if dme is None:
        ctx.dolphin_status = "dolphin_memory_engine is not installed; use /check and /goal"
        logger.info(ctx.dolphin_status)
        return
    while not ctx.exit_event.is_set():
        try:
            if not dme.is_hooked():
                dme.hook()
                if not dme.is_hooked():
                    ctx.dolphin_status = "waiting for Dolphin"
                    await asyncio.sleep(5)
                    continue
                region = ram.GAME_IDS.get(dme.read_bytes(0x80000000, 6))
                if region is None:
                    ctx.dolphin_status = "the game running in Dolphin is not Pokemon Channel"
                    dme.un_hook()
                    await asyncio.sleep(5)
                    continue
                ctx.dolphin_status = f"connected ({region})"
                logger.info(f"Dolphin {ctx.dolphin_status}.")
            if ctx.slot is not None:
                await _poll_game(ctx)
        except Exception as e:
            logger.info(f"Dolphin connection lost: {e}")
            ctx.dolphin_status = "connection lost"
            dme.un_hook()
        await asyncio.sleep(DOLPHIN_INTERVAL)


def main(*args: str) -> None:
    Utils.init_logging("PokemonChannelClient")

    async def _main(connect: Optional[str], password: Optional[str]) -> None:
        ctx = PokemonChannelContext(connect, password)
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        sync = asyncio.create_task(dolphin_sync_task(ctx), name="DolphinSync")
        await ctx.exit_event.wait()
        ctx.server_address = None
        await ctx.shutdown()
        sync.cancel()

    parser = get_base_parser()
    parser.add_argument("url", nargs="?", help="Archipelago connection url")
    parsed = handle_url_arg(parser.parse_args(args), parser=parser)

    import colorama

    colorama.just_fix_windows_console()
    asyncio.run(_main(parsed.connect, parsed.password))
    colorama.deinit()
