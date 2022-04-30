from __future__ import annotations

import os
import sys
from glob import glob

import discord
import git
from colorama import Fore, Style


def show_banner() -> None:
    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    with open("poetry.lock") as f:
        packages = f.read().count("[[package]]")
    fields: list[list[str, str, str]] = [
        ["Commit", sha[:7], Fore.YELLOW],
        ["Environment", os.getenv("ENVIRONMENT", "development"), Fore.GREEN],
        ["discord.py", discord.__version__, Fore.YELLOW],
        ["Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", Fore.BLUE],
        ["Scripts", len(glob("**/*.py", recursive=True)), Fore.CYAN],
        ["Packages", packages, Fore.LIGHTCYAN_EX],
        [
            "Extensions",
            len(list(filter(lambda f: f.endswith(".py") and not f.startswith("_"), os.listdir("src/exts/")))),
            Fore.LIGHTMAGENTA_EX,
        ],
    ]
    max_field_length = max(map(lambda field: len(field[0]), fields))
    print(Fore.CYAN + Style.BRIGHT + "+---------------------------------------+")
    print(Fore.LIGHTCYAN_EX + Style.BRIGHT + "  SevenBot" + Style.NORMAL + ": Multifunctional Discord bot")
    for raw_field_name, value, color in fields:
        bright = color.replace("[3", "[9")
        field_name = raw_field_name.ljust(max_field_length)
        print(f"    {color}{field_name}: {bright}{value}")
    print("")
    print(Fore.BLACK + "    (c) 2022 sevenc-nanashi,")
    print(Fore.BLACK + "               Licensed under GPLv3")
    print(Fore.CYAN + Style.BRIGHT + "+---------------------------------------+")
