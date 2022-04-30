import logging

from colorama import Fore, Style


class ColoredFormatter(logging.Formatter):
    FORMAT = "{} " + Fore.LIGHTBLACK_EX + "[%(name)s] %(asctime)s: " + Fore.BLACK + "%(message)s"

    def __init__(self, color):
        self.color = color
        logging.Formatter.__init__(
            self,
            "[%(name)s] %(levelname)s %(asctime)s: %(message)s",
        )

    def format(self, record):
        level_name = record.levelname
        color = ""
        level_modify = True
        if level_name == "DEBUG":
            color = Fore.LIGHTBLACK_EX
            level_name = "#"
        elif level_name == "INFO":
            color = Fore.LIGHTCYAN_EX
            level_name = "i"
        elif level_name == "WARNING":
            color = Fore.LIGHTYELLOW_EX
            level_name = "!"
        elif level_name == "ERROR":
            color = Fore.LIGHTRED_EX
            level_name = "x"
        elif level_name == "CRITICAL":
            color = Fore.LIGHTMAGENTA_EX
            level_name = "X"
        else:
            level_modify = False
        if level_modify:
            level_name = "(" + level_name + ")"
        if self.color:
            level_name = color + level_name + Style.RESET_ALL
        tmp_formatter = logging.Formatter(ColoredFormatter.FORMAT.format(level_name))
        return tmp_formatter.format(record)
