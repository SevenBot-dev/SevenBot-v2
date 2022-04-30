from enum import Flag
from typing import TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    from core import SevenBot


class CogFlag(Flag):
    production = 1
    development = 2


class Cog(commands.Cog):
    flag: CogFlag = CogFlag.production | CogFlag.development

    def __init__(self, bot: "SevenBot"):
        self.bot = bot
