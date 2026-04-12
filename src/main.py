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
from classes.youtube import YouTubeMenuController
from classes.twitter import TwitterMenuController
from classes.linkedin import LinkedInMenuController

youtube_controller = YouTubeMenuController()
twitter_controller = TwitterMenuController()
linkedin_controller = LinkedInMenuController()

def main():
    """Main entry point for the application, providing a menu-driven interface
        to manage YouTube, Twitter, and LinkedIn automation tasks.

        This function allows users to:
        1. Start the YouTube Shorts Automater to manage YouTube accounts,
           generate and upload videos, and set up CRON jobs.
        2. Start a Twitter Bot to manage Twitter accounts, post tweets, and
           schedule posts using CRON jobs.
        3. Start a LinkedIn Bot to manage LinkedIn accounts and automate
           LinkedIn-related tasks.
        4. Exit the application.t to manage LinkedIn activity.
        4. Exit the application.

        The function continuously prompts users for input, validates it, and
        executes the selected option until the user chooses to quit.

        Args:
            None

        Returns:
            None"""
    global user_input
    valid_input = False
    while not valid_input:
        try:
            print_banner()
            info("\n============ OPTIONS ============", False)

            for idx, option in enumerate(OPTIONS):
                print(colored(f" {idx + 1}. {option}", "cyan"))

            info("=================================\n", False)
            user_input = input("Select an option: ").strip()
            if user_input == '':
                raise ValueError("Empty input is not allowed.")
            user_input = int(user_input)
            valid_input = True
        except ValueError as e:
            print(f"Invalid input: {e}")

    match user_input:
        case 1:
            youtube_controller.run()

        case 2:
            twitter_controller.run()

        case 3:
            linkedin_controller.run()

        case 4:
            if get_verbose():
                print(colored(" => Quitting...", "blue"))
            sys.exit(0)
        case _:
            error("Invalid option selected. Please try again.", "red")
            main()

if __name__ == "__main__":

    # Print ASCII Banner
    print_banner()

    # Check first time run
    first_time = get_first_time_running()

    if first_time:
        info("Hey! It looks like you're running Auto Socials for the first time. Let's get you setup first!")

    # Run preflight checks
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

    # Setup file tree
    assert_folder_structure()

    # Remove temporary files
    #rem_temp_files()

    # Select model based on provider
    provider = get_llm_provider()
    model = get_default_model()

    if not model:
        error("No models found. Try running preflight_checks.py first.")
        raise SystemExit(1)

    while True:
        main()
