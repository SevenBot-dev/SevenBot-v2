import os
from discord.ext import commands


class SevenBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=["sb#", "sb."],
            help_command=None,
            strip_after_prefix=True,
            case_insensitive=True,
        )

    def run(self) -> None:
        """SevenBotを起動します。"""
        super(os.getenv("TOKEN"))

    @property
    def is_production(self) -> bool:
        """デプロイ中かを返します。"""
        return os.getenv("ENV", "development") == "production"
