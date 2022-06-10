from typing import TYPE_CHECKING

import discord
from discord import app_commands

from src.common.embed import LocaleEmbed

from ._common import Cog, CogFlag
from src.const.color import Color

if TYPE_CHECKING:
    from core import SevenBot


class Ping(Cog):
    flag = CogFlag.production | CogFlag.development

    @app_commands.command(name="ping", description="Pong!")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=LocaleEmbed(
                interaction.text("embed"),
                color=Color.sevenbot.value,
                latency=round(self.bot.latency * 1000),
            ),
            ephemeral=True,
        )


async def setup(bot: "SevenBot"):
    await bot.load_cog(Ping)
