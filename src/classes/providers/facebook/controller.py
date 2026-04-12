from classes.account_menu import BaseAccountMenuController
from classes.providers.facebook.service import FacebookService
from constants import COMMON_ACCOUNT_FIELDS
from status import error, info, question, success
from art import print_banner


class FacebookMenuController(BaseAccountMenuController):
    """
    Facebook-specific menu controller built on the shared account flow.
    """

    def __init__(self) -> None:
        super().__init__(
            provider="facebook",
            service_name="Facebook Automator",
            account_fields=COMMON_ACCOUNT_FIELDS,
        )

    def _build_service(self, account: dict) -> FacebookService:
        return FacebookService(
            account_uuid=account["id"],
            account_nickname=account["nickname"],
            firefox_profile_path=account["firefox_profile"],
            niche=account["niche"],
        )

    def run_account_session(self, account: dict) -> None:
        try:
            service = self._build_service(account)
        except KeyError as exc:
            error(f"Missing required account field: {exc}")
            return
        except ValueError as exc:
            error(str(exc))
            return
        except Exception as exc:
            error(f"Failed to start Facebook service: {exc}")
            return

        while True:
            print_banner()
            info("\n============ FACEBOOK OPTIONS ============", False)
            print(" 1. Test service")
            print(" 2. Generate video")
            print(" 3. Upload video")
            print(" 4. Show account details")
            print(" 5. Back")
            info("=========================================\n", False)

            user_input = question("Select an option: ").strip().lower()

            if user_input in {"5", "b", "back", "q", "quit"}:
                info("Returning to account menu...")
                return

            print_banner()

            if user_input == "1":
                service.test_connection()

            elif user_input == "2":
                service.generate_video()

            elif user_input == "3":
                service.upload_video()

            elif user_input == "4":
                self._show_account_details(account)

            else:
                error("Invalid option selected.")

            question("\nPress Enter to continue...", show_emoji=False)

    def _show_account_details(self, account: dict) -> None:
        success("Facebook account details:")
        for key, value in account.items():
            success(f" - {key}: {value}", show_emoji=False)
