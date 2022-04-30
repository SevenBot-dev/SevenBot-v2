import hashlib
import logging
import os
from base64 import b64decode
from typing import TYPE_CHECKING, Type

import discord
from discord.ext import commands, tasks

if TYPE_CHECKING:
    from .exts._common import Cog
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
            application_id=int(b64decode(os.environ["TOKEN"].split(".")[0]))
        )
        self.prev_hash = {}
        self.logger = logging.getLogger("SevenBot")

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

    @tasks.loop(seconds=10)
    async def watch_files(self) -> None:
        for file in os.listdir("src/exts/"):
            if not file.endswith(".py") or file.startswith("_"):
                continue
            with open(f"src/exts/{file}", "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            if file_hash != self.prev_hash.get(file):
                if self.prev_hash.get(file) is not None:
                    self.logger.info("Reloading %s by auto reloading", file)
                    await self.reload_extension(f"src.exts.{file[:-3]}")
                    await self.sync()
                self.prev_hash[file] = file_hash

    def run(self) -> None:
        """SevenBotを起動します。"""
        self.logger.info("Starting SevenBot...")
        super().run(os.environ["TOKEN"])

    def setup(self) -> None:
        pass

    async def sync(self) -> None:
        if self.is_production:
            guild = None
            self.logger.info("Syncing commands globally...")
        else:
            guild = discord.Object(int(os.environ["TEST_GUILD"]))
            self.logger.info("Syncing commands in %s...", guild)
        await self.tree.sync(guild=guild)

    async def load_cog(self, cog: Type["Cog"]) -> None:
        self.logger.info("Loading cog: %s", cog)
        if not (
            (cog.flag & CogFlag.production and self.is_production)
            or (cog.flag & CogFlag.development and not self.is_production)
        ):
            self.logger.info("Cog is not loaded: %s", cog)
            return
        await self.add_cog(cog(self), override=True)

    @property
    def is_production(self) -> bool:
        """デプロイ中かを返します。"""
        return os.getenv("environment", "development") == "production"
