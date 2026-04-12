from classes.providers.base_service import BaseProviderService
from status import info, success


class LinkedinService(BaseProviderService):
    """
    Service class for Linkedin automation.

    This should contain the actual Linkedin-specific logic such as:
    - browser/session startup
    - content generation
    - metadata generation
    - upload flow
    - account-specific Linkedin actions
    """

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        firefox_profile_path: str,
        niche: str,
    ) -> None:
        """
        Initialise the Linkedin service.

        Args:
            account_uuid (str): Unique identifier for the account.
            account_nickname (str): Friendly name for the account.
            firefox_profile_path (str): Firefox profile path used for login/session.
            niche (str): Account niche/category.
        """
        super().__init__(
            account_uuid=account_uuid,
            account_nickname=account_nickname,
            firefox_profile_path=firefox_profile_path,
            niche=niche,
        )

    def test_connection(self) -> None:
        """
        Stub method to verify the service is wired correctly.
        """
        success("Linkedin service started successfully.")
        info(f"UUID: {self.account_uuid}", False)
        info(f"Nickname: {self.account_nickname}", False)
        info(f"Niche: {self.niche}", False)
        info(f"Firefox Profile: {self.firefox_profile_path}", False)

    def generate_video(self) -> None:
        """
        Stub for future video generation logic.
        """
        info("generate_video() is not implemented yet.")

    def upload_video(self) -> None:
        """
        Stub for future upload logic.
        """
        info("upload_video() is not implemented yet.")
