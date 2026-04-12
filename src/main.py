import schedule
import subprocess
import json
import sys
import os
from termcolor import colored

from art import *
from config import *
from status import *
from constants import *

from classes.providers.youtube import YouTubeMenuController
from classes.providers.twitter import TwitterMenuController
from classes.providers.linkedin import LinkedinMenuController
from classes.providers.facebook import FacebookMenuController


MENU_CONTROLLERS = {
    1: YouTubeMenuController,
    2: TwitterMenuController,
    3: LinkedinMenuController,
    4: FacebookMenuController,
}

def run_startup_checks() -> None:
    """
    Runs startup checks and environment preparation.
    """
    print_banner()

    first_time = get_first_time_running()
    if first_time:
        info("Hey! It looks like you're running Auto Socials for the first time. Let's get you setup first!")

    info("Running preflight checks...")
    preflight_script = os.path.join(ROOT_DIR, "Scripts", "preflight_checks.py")

    try:
        subprocess.run([sys.executable, preflight_script], cwd=ROOT_DIR, check=True)
    except subprocess.CalledProcessError as exc:
        error(f"Preflight checks failed with exit code {exc.returncode}.")
        raise SystemExit(exc.returncode)
    except OSError as exc:
        error(f"Unable to run preflight checks: {exc}")
        raise SystemExit(1)

    assert_folder_structure()
    rem_temp_files()

def show_main_menu() -> int:
    """
    Displays the main menu and returns a validated integer selection.
    """
    while True:
        try:
            print_banner()
            info("\n============ OPTIONS ============", False)

            for idx, option in enumerate(OPTIONS, start=1):
                print(colored(f" {idx}. {option}", "cyan"))

            info("=================================\n", False)

            user_input = input("Select an option: ").strip()

            if not user_input:
                raise ValueError("Empty input is not allowed.")

            return int(user_input)

        except ValueError as exc:
            error(f"Invalid input: {exc}")


def run_selected_controller(selection: int) -> None:
    """
    Instantiates and runs the selected provider controller.
    """
    controller_class = MENU_CONTROLLERS.get(selection)

    if controller_class is None:
        error("Invalid option selected. Please try again.")
        return

    controller = controller_class()
    controller.run()


def main() -> None:
    """
    Main menu loop for Auto Socials.
    """
    while True:
        selection = show_main_menu()

        if selection == len(OPTIONS):
            info("Quitting...")
            raise SystemExit(0)

        run_selected_controller(selection)


if __name__ == "__main__":
    run_startup_checks()
    main()