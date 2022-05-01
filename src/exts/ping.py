from typing import TYPE_CHECKING

import discord
from discord import app_commands

from ._common import Cog, CogFlag

if TYPE_CHECKING:
    from core import SevenBot


class Ping(Cog):
    flag = CogFlag.production | CogFlag.development

    @app_commands.command(name="ping", description="Pong!")
    async def ping(self, interaction: discord.Interaction):
        self.logger.info("Hello!")
        await interaction.response.send_message("Pong!")


async def setup(bot: "SevenBot"):
    await bot.load_cog(Ping)
