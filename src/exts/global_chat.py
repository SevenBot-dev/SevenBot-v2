import asyncio
import hashlib
import re
from secrets import token_urlsafe
from typing import TYPE_CHECKING, Optional

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
SYSTEM_MESSAGE = "System"
LOGO = open("src/assets/global_chat.png", "rb").read()


class GlobalChat(Cog):
    flag = CogFlag.production | CogFlag.development
    group = app_commands.Group(name="global", description="グローバルチャット")

    def __init__(self, bot: "SevenBot"):
        super().__init__(bot)
        self.channels_cache = set()
        self.send_semaphore = asyncio.Semaphore(100)

    async def channels(self):
        if self.channels_cache:
            return self.channels_cache
        async for gc_room in self.bot.db.gc_room.find():
            self.channels_cache.update(gc_room["channels"])
        return self.channels_cache

    @group.command(name="activate", description="グローバルチャットに接続します。")
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

    @group.command(name="deactivate", description="グローバルチャットから切断します。")
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
        try:
            self.channels_cache.remove(interaction.channel_id)
        except KeyError:
            pass
        if len(current_room.channels) == 1:
            await self.bot.db.gc_room.delete_one({"id": current_room.id})
            embed = LocaleEmbed(interaction.text("deactivated_deleted"), name=current_room.name, id=current_room.id)
        else:
            await self.bot.db.gc_room.update_one(
                {"id": current_room.id}, {"$pull": {"channels": interaction.channel_id}}
            )
            current_room.channels.remove(interaction.channel_id)
            announce_embed = LocaleEmbed(
                interaction.text("leave_announce"), name=interaction.guild.name, count=len(current_room.channels)
            )
            if interaction.guild.icon:
                announce_embed.set_thumbnail(url=interaction.guild.icon.url)
            await self.multi_send(
                current_room,
                current_room.channels,
                embed=announce_embed,
                username=SYSTEM_MESSAGE,
            )
            embed = LocaleEmbed(interaction.text("deactivated"), name=current_room.name, id=current_room.id)
        webhook = await self.get_webhook(interaction.channel, current_room, create=False)
        if webhook is not None:
            await webhook.delete()
        await interaction.edit_original_message(
            embed=embed,
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
        self.channels_cache.add(interaction.channel_id)
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
        self.channels_cache.add(interaction.channel_id)
        gc_room.channels.append(interaction.channel_id)
        embed = LocaleEmbed(interaction.text("join_announce"), name=interaction.guild.name, count=len(gc_room.channels))
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        await self.multi_send(
            gc_room, gc_room.except_channel(interaction.channel_id), embed=embed, username=SYSTEM_MESSAGE
        )
        await final_interaction.edit_original_message(
            embed=LocaleEmbed(interaction.guild_text("join_success"), name=gc_room.name, id=gc_room.id),
            view=None,
        )

    async def multi_send(self, gc_room: GlobalChatRoom, channels: list[int], **kwargs) -> list[discord.WebhookMessage]:
        def get_coroutine(channel_id: int):
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                return
            return self.single_send(gc_room, channel, **kwargs)

        return await asyncio.gather(*filter(lambda c: c, map(get_coroutine, channels)))

    async def single_send(
        self, gc_room: GlobalChatRoom, channel: discord.TextChannel, **kwargs
    ) -> discord.WebhookMessage:
        webhook = await self.get_webhook(channel, gc_room, create=True)
        if webhook is None:
            return
        async with self.send_semaphore:
            return await webhook.send(**kwargs, allowed_mentions=discord.AllowedMentions.none(), wait=True)

    async def get_webhook(
        self, channel: discord.TextChannel, gc_room: GlobalChatRoom, create: bool = False
    ) -> Optional[discord.Webhook]:
        webhook = await channel.webhooks()
        name = f"sevenbot-global-webhook-{gc_room.id}"
        for w in webhook:
            if w.name == name:
                return w
        if not create:
            return None
        try:
            return await channel.create_webhook(name=name, avatar=LOGO)
        except discord.HTTPException:
            return None

    @commands.Cog.listener("on_valid_message")
    async def on_message_global(self, message: discord.Message):
        if message.channel.id not in await self.channels():
            return
        db_data = await self.bot.db.gc_room.find_one({"channels": message.channel.id})
        if db_data is None:
            return
        gc_room = GlobalChatRoom.from_dict(db_data)
        name = str(message.author)
        suffix = f"(From {message.guild.name}, ID: {message.author.id})"
        if len(name + " " + suffix) > 80:
            name = name[: 80 - len(suffix)]
        name += " " + suffix
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
        self.bot.loop.create_task(message.add_reaction(self.bot.emoji("clock")))
        await self.multi_send_filtered(
            gc_room,
            gc_room.except_channel(message.channel.id),
            content=message.clean_content,
            username=name,
            avatar_url=message.author.display_avatar,
            embeds=embeds,
        )
        self.bot.loop.create_task(message.remove_reaction(self.bot.emoji("clock"), self.bot.user))
        self.bot.loop.create_task(message.add_reaction(self.bot.emoji("check")))
        await asyncio.sleep(3)
        await message.remove_reaction(self.bot.emoji("check"), self.bot.user)

    def get_size(self, size: int):
        if size < 1024:
            return f"{size} Bytes"
        elif size < 1048576:
            return f"{size / 1024} KiB"
        elif size < 1073741824:
            return f"{size / 1048576} MiB"
        else:
            return f"{size / 1073741824} GiB"

    async def multi_send_filtered(self, gc_room: GlobalChatRoom, channels: list[int], content, **kwargs):
        if len(content.splitlines()) > 10:
            content = "\n".join(content.splitlines()[:10]) + "\n..."
        content = INVITE_PATTERN.sub("", content)
        return await self.multi_send(gc_room, channels, content=content, **kwargs)


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
