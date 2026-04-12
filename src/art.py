import os
from config import ROOT_DIR
from termcolor import colored

def print_banner() -> None:
    """
    Prints the introductory ASCII Art Banner.
    Clears the screen and prints the banner.

    Returns:
        None
    """
    os.system("cls" if os.name == "nt" else "clear")
    with open(f"{ROOT_DIR}/assets/banner.txt", "r") as file:
        print(colored(file.read(), "green"))
