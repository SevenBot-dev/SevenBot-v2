from typing import TYPE_CHECKING
import discord
from discord.ext import commands

from ._common import Cog

if TYPE_CHECKING:
    from core import SevenBot


class ExtraEvents(Cog):
    @commands.Cog.listener("on_message")
    async def on_valid_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        self.bot.dispatch("valid_message", message)


async def setup(bot: "SevenBot"):
    await bot.load_cog(ExtraEvents)
