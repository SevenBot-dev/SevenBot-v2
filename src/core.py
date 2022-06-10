import json
import logging
import os
from base64 import b64decode
from typing import TYPE_CHECKING, Type

import discord
from discord.ext import commands, tasks
from motor import motor_asyncio as motor

if TYPE_CHECKING:
    from .exts._common import Cog

from . import lang  # noqa: F401
from .exts._common import CogFlag


class SevenBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        intents.typing = False
        super().__init__(
            command_prefix=["sb#", "sb."],
            help_command=None,
            strip_after_prefix=True,
            case_insensitive=True,
            intents=intents,
            application_id=int(b64decode(os.environ["TOKEN"].split(".")[0])),
        )
        self.prev_update = {}
        self.prev_commands = []
        self.logger = logging.getLogger("SevenBot")
        self.db_client = motor.AsyncIOMotorClient(os.environ["MONGO_URI"])
        self.db = self.db_client["production" if self.is_production else "development"]

    async def on_ready(self) -> None:
        """bot起動時のイベント"""
        self.logger.info("SevenBot is ready.")

    async def setup_hook(self) -> None:
        for file in os.listdir("src/exts/"):
            if not file.endswith(".py") or file.startswith("_"):
                continue
            name = file[:-3]
            await self.load_extension(f"src.exts.{name}")
        await self.sync()
        self.watch_files.start()

    @tasks.loop(seconds=1)
    async def watch_files(self) -> None:
        try:
            for file in os.listdir("src/exts/"):
                if not file.endswith(".py") or file.startswith("_"):
                    continue
                update_time = os.path.getmtime(f"src/exts/{file}")
                if update_time != self.prev_update.get(file):
                    if self.prev_update.get(file) is not None:
                        self.logger.info("Reloading %s by auto reloading", file)
                        try:
                            await self.reload_extension(f"src.exts.{file[:-3]}")
                        except commands.errors.ExtensionNotLoaded:
                            await self.load_extension(f"src.exts.{file[:-3]}")
                        await self.sync()
                    self.prev_update[file] = update_time
        except Exception as e:
            self.logger.exception(e)

    def run(self) -> None:
        """SevenBotを起動します。"""
        self.logger.info("Starting SevenBot...")
        super().run(os.environ["TOKEN"])

    def setup(self) -> None:
        pass

    @property
    def test_guild(self):
        return discord.Object(int(os.environ["TEST_GUILD"]))

    async def sync(self) -> None:
        current_commands = list(self.tree.walk_commands(guild=self.test_guild))
        if sorted([c.to_dict() for c in self.prev_commands], key=lambda c: json.dumps(c)) == sorted(
            [c.to_dict() for c in current_commands], key=lambda c: json.dumps(c)
        ):
            self.logger.info("No changes, skipping sync")
            return
        self.prev_commands = current_commands
        if self.is_production:
            guild = None
            self.logger.info("Syncing commands globally...")
        else:
            guild = self.test_guild
            self.logger.info("Syncing %d commands in %s...", len(current_commands), guild.id)

        await self.tree.sync(guild=guild)

    async def load_cog(self, cog: Type["Cog"]) -> None:
        self.logger.info("Loading cog: %s", cog)
        if not (
            (cog.flag & CogFlag.production and self.is_production)
            or (cog.flag & CogFlag.development and not self.is_production)
        ):
            self.logger.info("Cog is not loaded: %s", cog)
            return
        if self.is_production:
            guild = None
        else:
            guild = self.test_guild
        await self.add_cog(cog(self), override=True, guild=guild)

    @property
    def is_production(self) -> bool:
        """デプロイ中かを返します。"""
        return os.getenv("environment", "development") == "production"
