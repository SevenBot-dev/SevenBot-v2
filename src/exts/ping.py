from typing import TYPE_CHECKING

import discord
from discord import app_commands

from ._common import Cog, CogFlag
from src.const.color import Color

if TYPE_CHECKING:
    from core import SevenBot


class Ping(Cog):
    flag = CogFlag.production | CogFlag.development

    @app_commands.command(name="ping", description="Pong!")
    async def ping(self, interaction: discord.Interaction):
        self.logger.info("Hello!")
        await interaction.response.send_message(
            embed=discord.Embed(
                title=interaction.text("embed.title"),
                description=interaction.text("embed.description", latency=round(self.bot.latency * 1000)),
                color=Color.sevenbot.value,
            ),
            ephemeral=True,
        )


async def setup(bot: "SevenBot"):
    await bot.load_cog(Ping)
