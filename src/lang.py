import os
import discord
import yaml


def get_locale(locale: discord.Locale) -> str:
    locale = locale.value.split("-")[0]
    if os.path.exists(f"locale/{locale}.yml"):
        return f"locale/{locale}.yml"
    else:
        return "locale/en.yml"


def text(self: discord.Interaction, code: str, **formats) -> str:
    try:
        with open(get_locale(self.locale), "r", encoding="utf-8") as file:
            texts = yaml.safe_load(file)
        command = self.command
        if isinstance(self.command, discord.app_commands.Command):
            if not command.parent:
                base = texts["chat_input"][command.name]
            elif command.parent == command.root_parent:  # Subcommand
                base = texts["chat_input"][command.parent.name][command.name]
            else:  # Subcommand group
                base = texts["chat_input"][command.root_parent.name][command.parent.name][command.name]
        else:  # Context
            base = texts["context"][str(self.command)]
        for code_key in code.split("."):
            base = base[code_key]
        return base.format(**formats)
    except KeyError:
        return f"*{code}*"


def guild_text(self: discord.Interaction, code: str, **formats) -> str:
    try:
        with open(get_locale(self.guild_locale), "r", encoding="utf-8") as file:
            texts = yaml.safe_load(file)
        command = self.command
        if command.type == discord.AppCommandType.chat_input:
            if not command.parent:
                base = texts["chat_input"][command.name]
            elif command.parent == command.root_parent:  # Subcommand
                base = texts["chat_input"][command.parent.name][command.name]
            else:  # Subcommand group
                base = texts["chat_input"][command.root_parent.name][command.parent.name][command.name]
        else:
            base = texts["context"][str(self.command)]
        for code_key in code.split("."):
            base = base[code_key]
        return base.format(**formats)
    except KeyError:
        return f"*{code}*"


discord.Interaction.text = text  # Monkey patch
discord.Interaction.guild_text = guild_text
