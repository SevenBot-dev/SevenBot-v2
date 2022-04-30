import logging

from colorama import init
from dotenv import load_dotenv

from src.console import show_banner
from src.core import SevenBot
from src.formatter import ColoredFormatter


def setup_logging():
    discord_logger = logging.getLogger("discord")
    sevenbot_logger = logging.getLogger("SevenBot")
    discord_logger.setLevel(logging.DEBUG)
    sevenbot_logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler(filename="sevenbot.log", encoding="utf-8", mode="w")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    discord_logger.addHandler(file_handler)
    sevenbot_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter(True))
    discord_logger.addHandler(console_handler)
    sevenbot_logger.addHandler(console_handler)


def main():
    init(autoreset=True)
    load_dotenv()
    sevenbot = SevenBot()

    setup_logging()
    show_banner()
    sevenbot.setup()
    sevenbot.run()


if __name__ == "__main__":
    main()
