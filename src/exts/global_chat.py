from typing import TYPE_CHECKING

import discord
from discord import app_commands

from ._common import Cog, CogFlag

if TYPE_CHECKING:
    from core import SevenBot


class GlobalChat(Cog):
    flag = CogFlag.production | CogFlag.development
    group = app_commands.Group(name="global", description="グローバルチャット")

    @group.command(name="activate", description="Activate global chat")
    async def activate(self, interaction: discord.Interaction):
        print("Activate global chat!")
        await interaction.response.defer()


async def setup(bot: "SevenBot"):
    await bot.load_cog(GlobalChat)
