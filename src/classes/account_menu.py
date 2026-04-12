from uuid import uuid4

from prettytable import PrettyTable
from termcolor import colored

from art import print_banner
from cache import add_account, get_accounts, remove_account
from config import get_firefox_profile_path
from status import error, info, question, success, warning


class BaseAccountMenuController:
    """Shared account menu flow used by provider-specific controllers."""

    def __init__(self, provider: str, service_name: str, account_fields: list[tuple[str, str]]) -> None:
        self.provider = provider
        self.service_name = service_name
        self.account_fields = account_fields

    def run(self) -> None:
        while True:
            print_banner()
            info(f"Starting {self.service_name}...")
            accounts = get_accounts(self.provider)
            if not accounts:
                if not self._handle_empty_accounts():
                    return
                continue

            action, account = self._show_accounts(accounts)
            if action == "back":
                info("Returning to main menu...")
                return
            if action == "refresh":
                continue

            selected_account = account
            success(
                f"Selected account: "
                f"{selected_account.get('nickname', selected_account.get('id', 'Unknown'))}"
            )
            self.test_service(selected_account)
            question("Press Enter to return to account menu...", show_emoji=False)
            continue

    def _handle_empty_accounts(self) -> bool:
        while True:
            print_banner()
            info(f"Starting {self.service_name}...")
            warning("No accounts found in cache. Create one now?")
            create_now = question("Yes/No (or 'b' to return): ").strip().lower()

            if create_now in {"yes", "y"}:
                return self._create_account()

            if create_now in {"no", "n", "b", "back", "q", "quit"}:
                info("Returning to main menu...")
                return False

            error("Invalid option. Enter yes, no, or b.")

    def _create_account(self) -> bool:
        generated_uuid = str(uuid4())
        success(f" => Generated ID: {generated_uuid}")

        account = {
            "id": generated_uuid,
            "firefox_profile": get_firefox_profile_path(),
            "videos": [],
        }

        for key, prompt in self.account_fields:
            value = self._ask_for_field(prompt)
            if value is None:
                info("Account creation cancelled. Returning to main menu...")
                return False
            account[key] = value

        add_account(self.provider, account)
        success("Account configured successfully!")
        return True

    def _ask_for_field(self, prompt: str) -> str | None:
        while True:
            print_banner()
            info(f"Starting {self.service_name}...")
            value = question(f" => Enter {prompt} (or 'b' to return): ").strip()
            if value.lower() in {"b", "back", "q", "quit"}:
                return None
            if value:
                return value
            error("This field cannot be empty.")

    def _show_accounts(self, accounts: list[dict]) -> tuple[str, dict | None]:
        info(f"Cached {self.service_name} accounts found:")
        table = PrettyTable()
        table.field_names = ["ID", "UUID", "Nickname", "Niche"]

        for idx, account in enumerate(accounts, start=1):
            table.add_row([
                idx,
                colored(account.get("id", ""), "cyan"),
                colored(account.get("nickname", ""), "blue"),
                colored(account.get("niche", ""), "green"),
            ])

        print(table)
        selection = question(
            "Select an account to start "
            "(or 'd' to delete, 'n' to create new account, 'b' to return): "
        ).strip().lower()

        if selection in {"b", "back", "q", "quit"}:
            return "back", None

        if selection == "n":
            if self._create_account():
                return "refresh", None
            return "back", None

        if selection == "d":
            self._delete_account(accounts)
            return "refresh", None

        try:
            selected_index = int(selection) - 1
        except ValueError:
            error("Invalid account selection.")
            return "refresh", None

        if selected_index < 0 or selected_index >= len(accounts):
            error("Account index out of range.")
            return "refresh", None

        return "selected", accounts[selected_index]

    def _delete_account(self, accounts: list[dict]) -> None:
        print_banner()
        info(f"Starting {self.service_name}...")
        info(f"Cached {self.service_name} accounts found:")
        table = PrettyTable()
        table.field_names = ["ID", "UUID", "Nickname", "Niche"]

        for idx, account in enumerate(accounts, start=1):
            table.add_row([
                idx,
                colored(account.get("id", ""), "cyan"),
                colored(account.get("nickname", ""), "blue"),
                colored(account.get("niche", ""), "green"),
            ])

        print(table)
        selection = question("Enter account ID number to delete (or 'b' to return): ").strip().lower()
        if selection in {"b", "back", "q", "quit"}:
            return

        try:
            selected_index = int(selection) - 1
        except ValueError:
            error("Invalid account index.")
            return

        if selected_index < 0 or selected_index >= len(accounts):
            error("Account index out of range.")
            return

        account = accounts[selected_index]
        removed = remove_account(self.provider, account.get("id", ""))
        if removed:
            success(f"Deleted account: {account.get('nickname', account.get('id', 'Unknown'))}")
            return

        error("Failed to delete account.")

    def test_service(self, account: dict) -> None:
        raise NotImplementedError

