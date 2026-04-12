from classes.account_menu import BaseAccountMenuController
from status import success


class TwitterMenuController(BaseAccountMenuController):
    """Twitter-specific menu controller built on the shared account flow."""

    def __init__(self) -> None:
        super().__init__(
            provider="twitter",
            service_name="Twitter Bot",
            account_fields=[
                ("nickname", "a nickname for this account"),
                ("niche", "the account niche"),
            ],
        )

    def test_service(self, account: dict) -> None:
        success("Twitter service is running with selected account:")
        for key, value in account.items():
            success(f" - {key}: {value}", show_emoji=False)
