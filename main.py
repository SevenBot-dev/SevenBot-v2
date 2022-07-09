import logging

from colorama import init
from dotenv import load_dotenv

from src.console import show_banner
from src.core import SevenBot
from src.formatter import ColoredFormatter


def setup_logging():
    file_handler = logging.FileHandler(filename="sevenbot.log", encoding="utf-8", mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter(True))

    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(file_handler)
    logging.root.addHandler(console_handler)


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
