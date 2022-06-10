import asyncio
import hashlib
import re
from secrets import token_urlsafe
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ui import Modal, TextInput
from discord.ext import commands
from src.db.gc_room import GlobalChatRoom
from src.common.embed import LocaleEmbed
from src.common.confirm import ConfirmView

from ._common import Cog, CogFlag

if TYPE_CHECKING:
    from core import SevenBot


INVITE_PATTERN = re.compile(r"(?:https?://)?discord(?:app\.com/invite|\.gg)/[a-z0-9]+", re.I)
FILE_COLORS = {
    "application": discord.Color.blurple(),
    "audio": discord.Color.green(),
    "font": discord.Color.dark_teal(),
    "image": discord.Color.dark_orange(),
    "text": discord.Color.dark_purple(),
    "video": discord.Color.dark_red(),
    "zip": discord.Color.dark_gold(),
    "model": discord.Color.dark_magenta(),
}


class GlobalChat(Cog):
    flag = CogFlag.production | CogFlag.development
    group = app_commands.Group(name="global", description="グローバルチャット")

    def __init__(self, bot: "SevenBot"):
        super().__init__(bot)
        self._channels_cache = set()

    async def channels(self):
        if self._channels_cache:
            return self._channels_cache
        async for gc_room in self.bot.db.gc_room.find():
            self._channels_cache.update(gc_room["channels"])
        return self._channels_cache

    @group.command(name="activate", description="グローバルチャットを有効にします。")
    @app_commands.describe(gc_id="接続するグローバルチャットの名前。")
    @app_commands.rename(gc_id="id")
    async def activate(self, interaction: discord.Interaction, gc_id: str = "global"):
        await interaction.response.defer(ephemeral=True)
        current_room = await self.bot.db.gc_room.find_one({"channels": interaction.channel_id})
        if current_room is not None:
            current_room = GlobalChatRoom.from_dict(current_room)
            await interaction.followup.send(
                embed=LocaleEmbed(interaction.text("already_in"), name=current_room.name, id=current_room.id),
                ephemeral=True,
            )
            return
        gc_room = await self.bot.db.gc_room.find_one({"id": gc_id})
        if gc_room is None:
            await self.create_gc_room(interaction, gc_id)
        else:
            await self.join_gc_room(interaction, GlobalChatRoom.from_dict(gc_room))

    @group.command(name="deactivate", description="Deactivate global chat")
    async def deactivate(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        current_room = await self.bot.db.gc_room.find_one({"channels": interaction.channel_id})
        if current_room is None:
            await interaction.followup.send(
                embed=LocaleEmbed(interaction.text("not_in")),
                ephemeral=True,
            )
            return
        current_room = GlobalChatRoom.from_dict(current_room)
        confirm = ConfirmView(lang=interaction.locale, button_color=discord.ButtonStyle.danger)
        await interaction.followup.send(
            embed=LocaleEmbed(interaction.text("deactivate_confirm"), name=current_room.name, id=current_room.id),
            view=confirm,
            ephemeral=True,
        )
        await confirm.wait()
        if confirm.value is None:
            return await interaction.followup.send(
                interaction.text("common.timeouted"),
                ephemeral=True,
            )
        if not confirm.value:
            return await confirm.interaction.response.send_message(
                interaction.text("common.canceled"),
                ephemeral=True,
            )
        await self.bot.db.gc_room.delete_one({"id": current_room.id})
        self._channels_cache.remove(interaction.channel_id)
        await interaction.edit_original_message(
            embed=LocaleEmbed(interaction.text("deactivated"), name=current_room.name, id=current_room.id),
            ephemeral=True,
            view=None,
        )

    async def create_gc_room(self, interaction: discord.Interaction, gc_id: str):
        confirm = ConfirmView(
            lang=interaction.locale,
            button_color=discord.ButtonStyle.success,
        )
        await interaction.edit_original_message(
            embed=LocaleEmbed(interaction.text("create_confirm"), name=gc_id),
            view=confirm,
        )
        await confirm.wait()
        if confirm.value is None:
            return await interaction.followup.send(
                interaction.text("common.timeouted"),
                ephemeral=True,
            )
        if not confirm.value:
            return await confirm.interaction.response.send_message(
                interaction.text("common.canceled"),
                ephemeral=True,
            )
        modal = CreateModal(confirm.interaction, gc_id)
        await confirm.interaction.response.send_modal(modal)
        await modal.wait()
        modal_interaction = modal.interaction
        response = {}
        for component in modal_interaction.data["components"]:
            response[component["components"][0]["custom_id"].split(":")[1]] = component["components"][0]["value"]
        room = GlobalChatRoom(
            id=gc_id,
            name=response["name"],
            channels=[interaction.channel_id],
            owner=interaction.user.id,
            password=hashlib.sha256(response["password"].encode("utf-8")).hexdigest() if response["password"] else None,
            description=response["description"],
            mute=[],
            rule={},
            slow=0,
            antispam=False,
        )
        await modal_interaction.response.defer(
            ephemeral=True,
        )
        await self.bot.db.gc_room.insert_one(room.to_dict())
        self._channels_cache.add(interaction.channel_id)
        await modal_interaction.edit_original_message(
            embed=LocaleEmbed(
                interaction.text("create_success"),
                id=gc_id,
                name=response["name"],
            ),
            view=None,
        )

    async def join_gc_room(self, interaction: discord.Interaction, gc_room: GlobalChatRoom):
        confirm = ConfirmView(
            lang=interaction.locale,
            button_color=discord.ButtonStyle.success,
        )
        await interaction.edit_original_message(
            embed=LocaleEmbed(
                interaction.text("join_confirm"),
                name=gc_room.name,
                id=gc_room.id,
                description=gc_room.description,
            ),
            view=confirm,
        )
        await confirm.wait()
        if confirm.value is None:
            return await interaction.followup.send(
                interaction.text("common.timeouted"),
                ephemeral=True,
            )
        if not confirm.value:
            return await confirm.interaction.response.send_message(
                interaction.text("common.canceled"),
                ephemeral=True,
            )
        if gc_room.password:
            modal = PasswordModal(confirm.interaction)
            await confirm.interaction.response.send_modal(modal)
            await modal.wait()
            final_interaction = modal.interaction
            password = final_interaction.data["components"][0]["components"][0]["value"]
            if gc_room.password != hashlib.sha256(password.encode("utf8")).hexdigest():
                await final_interaction.response.send_message(
                    embed=LocaleEmbed(interaction.text("password_failed")),
                    ephemeral=True,
                )
                return
        else:
            final_interaction = confirm.interaction
        await final_interaction.response.defer(
            ephemeral=True,
        )
        await self.bot.db.gc_room.update_one(
            {"id": gc_room.id},
            {"$addToSet": {"channels": interaction.channel_id}},
        )
        self._channels_cache.add(interaction.channel_id)
        embed = LocaleEmbed(
            interaction.text("join_announce"), name=interaction.guild.name, count=len(gc_room.channels) + 1
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        await self.multi_send(
            gc_room,
            embed=embed,
        )
        await final_interaction.response.send_message(
            embed=LocaleEmbed(interaction.text("join_success")),
            ephemeral=True,
        )

    async def multi_send(self, gc_room: GlobalChatRoom, **kwargs):
        def get_coroutine(channel_id: int):
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                return
            self.single_send(gc_room, channel, **kwargs)

        await asyncio.gather(filter(lambda c: c, map(get_coroutine, gc_room.channels)))

    async def single_send(self, gc_room: GlobalChatRoom, channel: discord.TextChannel, **kwargs):
        webhook = await self.get_webhook(channel, gc_room)
        if webhook is None:
            return
        await webhook.send(**kwargs)

    async def get_webhook(self, channel: discord.TextChannel, gc_room: GlobalChatRoom):
        webhook = await channel.webhooks()
        name = f"sevenbot-global-webhook-{gc_room.id}"
        for w in webhook:
            if w.name == name:
                return w
        try:
            return await channel.create_webhook(name=name)
        except discord.HTTPException:
            return None

    @commands.Cog.listener("on_valid_message")
    async def on_message_global(self, message: discord.Message):
        if message.channel.id not in await self.channels():
            return
        db_data = await self.bot.db.gc_room.find_one({"channel": message.channel.id})
        if db_data is None:
            return
        gc_room = GlobalChatRoom.from_dict(db_data)
        name = message.author.display_name
        suffix = f"(From {message.guild.name}, ID: {message.author.id})"
        if len(name) + len(suffix) > 32:
            name = name[: 32 - len(suffix)]
        name += suffix
        embeds = []
        for attachment in message.attachments:
            if attachment.content_type:
                content_type = attachment.content_type
            else:
                content_type = "application/octet-stream"
            embed = discord.Embed(
                title=attachment.name + " (" + self.get_size(attachment.size) + ")",
                url=attachment.url,
                color=FILE_COLORS[content_type.split("/")[0]],
            )
            if content_type.startswith("image/"):
                embed.set_image(url=attachment.url)
            embeds.append(embed)
        await self.multi_send_filtered(
            gc_room,
            content=message.clean_content,
            username=name,
            avatar_url=message.author.display_avatar,
            embeds=embeds,
        )

    def get_size(self, size: int):
        if size < 1024:
            return f"{size} Bytes"
        elif size < 1048576:
            return f"{size / 1024} KiB"
        elif size < 1073741824:
            return f"{size / 1048576} MiB"
        else:
            return f"{size / 1073741824} GiB"

    async def multi_send_filtered(self, gc_room: GlobalChatRoom, content, **kwargs):
        if len(content.splitlines()) > 10:
            content = "\n".join(content.splitlines()[:10]) + "\n..."
        content = INVITE_PATTERN.sub("", content)
        await self.multi_send(gc_room, content=content, **kwargs)


class CreateModal(Modal):
    def __init__(self, interaction: discord.Interaction, name: str):
        command_texts = interaction.text("chat_input.global.activate.create")
        super().__init__(title=command_texts("title"))
        field_texts = command_texts("fields")
        self.nonce: str = token_urlsafe(16)
        self.interaction = None
        self.add_item(
            TextInput(
                label=field_texts("name.name"),
                placeholder=field_texts("name.placeholder"),
                default=name,
                custom_id=self.nonce + ":name",
            )
        )
        self.add_item(
            TextInput(
                label=field_texts("description.name"),
                placeholder=field_texts("description.placeholder"),
                default="",
                style=discord.TextStyle.paragraph,
                custom_id=self.nonce + ":description",
            )
        )
        self.add_item(
            TextInput(
                label=field_texts("password.name"),
                placeholder=field_texts("password.placeholder"),
                default="",
                custom_id=self.nonce + ":password",
                required=False,
            )
        )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction
        self.stop()


class PasswordModal(Modal):
    def __init__(self, interaction: discord.Interaction):
        command_texts = interaction.text("chat_input.global.activate.join_password")
        super().__init__(title=command_texts("title"))
        field_texts = command_texts("fields")
        self.nonce: str = token_urlsafe(16)
        self.interaction = None
        self.add_item(
            TextInput(
                label=field_texts("password.name"),
                placeholder=field_texts("password.placeholder"),
                default="",
                custom_id=self.nonce + ":password",
                required=True,
            )
        )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.interaction = interaction
        self.stop()


async def setup(bot: "SevenBot"):
    await bot.load_cog(GlobalChat)
