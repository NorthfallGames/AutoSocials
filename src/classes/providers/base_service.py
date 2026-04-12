import os


class BaseProviderService:
    """
    Shared base service for provider automation classes.

    This class contains the common account/service fields and validation
    used by all providers such as YouTube, Twitter, and LinkedIn.
    """

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        firefox_profile_path: str,
        niche: str,
    ) -> None:
        """
        Initialise shared provider service data.

        Args:
            account_uuid (str): Unique identifier for the account.
            account_nickname (str): Friendly name for the account.
            firefox_profile_path (str): Firefox profile path used for login/session.
            niche (str): Account niche/category.
        """
        self.account_uuid = account_uuid
        self.account_nickname = account_nickname
        self.firefox_profile_path = firefox_profile_path
        self.niche = niche

        self.validate_common_fields()

    def validate_common_fields(self) -> None:
        """
        Validate the shared account fields required by all providers.

        Raises:
            ValueError: If any required field is invalid.
        """
        if not isinstance(self.account_uuid, str) or not self.account_uuid.strip():
            raise ValueError("Account UUID cannot be empty.")

        if not isinstance(self.account_nickname, str) or not self.account_nickname.strip():
            raise ValueError("Account nickname cannot be empty.")

        if not isinstance(self.niche, str) or not self.niche.strip():
            raise ValueError("Account niche cannot be empty.")

        if not isinstance(self.firefox_profile_path, str) or not self.firefox_profile_path.strip():
            raise ValueError("Firefox profile path cannot be empty.")

        if not os.path.isdir(self.firefox_profile_path):
            raise ValueError(
                "Firefox profile path does not exist or is not a directory: "
                f"{self.firefox_profile_path}"
            )