from calendar import c
import discord
from enum import Enum


class Color(Enum):
    sevenbot = discord.Color(0x00CCFF)
    error = discord.Color.red()
    success = discord.Color.green()
    info = discord.Color.blue()
    warning = discord.Color.orange()
