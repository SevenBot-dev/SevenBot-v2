from logging import getLogger
import os
from typing import Any
import discord
import yaml

from src.common.missing import MISSING


logger = getLogger("lang")


class DefaultMap(dict):
    def __missing__(self, key):
        return key.join("{}")


class LocaleGroup:
    def __init__(self, code: str, data: str, lang: str):
        self.code = code
        self.data = data
        self.lang = lang

    def __call__(self, code: str, default: Any = MISSING, **formats) -> str:
        try:
            base = self.data
            for part in code.split("."):
                base = base[part]
        except KeyError:
            if default is MISSING:
                logger.warning(f"Missing text in LocaleGroup: {self.lang}/{self.code}.{code}")
                return LocaleText(f"*{self.code}.{code}*", self.lang)
            return default
        else:
            if isinstance(base, str):
                return LocaleText(base.format_map(DefaultMap(formats)), self.lang)
            return LocaleGroup(self.code + "." + code, base, self.lang)


class LocaleText(str):
    def __new__(cls, text: str, lang: str):
        obj = str.__new__(cls, text)
        obj.lang = lang
        return obj

    @property
    def code(self):
        return self.replace("*", "")

    def __call__(self, code: str, default: Any = MISSING, **formats):
        if default is not MISSING:
            return default
        logger.warning(f"Missing text in LocaleText: {self.lang}/{self.code}.{code}")
        return LocaleText(f"*{self.code}.{code}*", self.lang)


def get_texts(locale: str) -> dict:
    with open(get_locale(locale), "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_locale(locale: str) -> str:
    locale = locale.value.split("-")[0]
    if os.path.exists(f"locale/{locale}.yml"):
        return f"locale/{locale}.yml"
    else:
        return "locale/en.yml"


def interaction_text(self: discord.Interaction, code: str, **formats) -> str:
    texts = get_texts(self.locale)
    command = self.command
    if code.split(".")[0] in texts:
        pass
    elif isinstance(command, discord.app_commands.Command):
        code = "chat_input." + command.qualified_name.replace(" ", ".") + "." + code
    else:  # Context
        code = "context." + str(command) + "." + code
    return text(self.locale, code, **formats)


def interaction_guild_text(self: discord.Interaction, code: str, **formats) -> str:
    texts = get_texts(self.guild_locale)
    command = self.command
    if code.split(".")[0] in texts:
        pass
    elif isinstance(command, discord.app_commands.Command):
        code = "chat_input." + command.qualified_name.replace(" ", ".") + "." + code
    else:  # Context
        code = "context." + str(command) + "." + code
    return text(self.guild_locale, code, **formats)


def text(lang: str, code: str, **formats) -> str:
    try:
        texts = get_texts(lang)
        base = texts
        for code_key in code.split("."):
            base = base[code_key]
    except KeyError:
        logger.warning(f"Missing text: {lang}/{code}")
        return LocaleText(f"*{code}*", lang)
    else:
        if isinstance(base, str):
            return LocaleText(base.format_map(DefaultMap(formats)), lang)
        return LocaleGroup(code, base, lang)


discord.Interaction.text = interaction_text  # Monkey patch
discord.Interaction.guild_text = interaction_guild_text
