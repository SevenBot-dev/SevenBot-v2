from __future__ import annotations

from secrets import token_urlsafe

import discord
from discord.ui import Button, View
from src.lang import text


class ConfirmView(View):
    def __init__(
        self,
        lang: str,
        cancel_first: bool = False,
        button_color: discord.ButtonStyle = discord.ButtonStyle.primary,
    ):
        super().__init__(timeout=30)
        self.value: bool | None = None
        self.nonce: str = token_urlsafe(16)
        self.interaction: discord.Interaction = None
        confirm_button = Button(
            label=text(lang, "common.confirm"),
            style=button_color,
            row=0,
            custom_id=self.nonce + ":confirm",
        )
        cancel_button = Button(
            label=text(lang, "common.cancel"),
            style=discord.ButtonStyle.secondary,
            row=0,
            custom_id=self.nonce + ":cancel",
        )
        confirm_button.callback = self.callback
        cancel_button.callback = self.callback

        if cancel_first:
            self.add_item(
                cancel_button,
            )
            self.add_item(confirm_button)
        else:
            self.add_item(confirm_button)
            self.add_item(cancel_button)

    async def on_timeout(self) -> None:
        self.stop()

    async def callback(self, interaction: discord.Interaction):
        self.value = interaction.data["custom_id"].split(":")[1] == "confirm"

        self.interaction = interaction
        self.stop()
