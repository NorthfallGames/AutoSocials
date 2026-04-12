from classes.providers.base_service import BaseProviderService
from importlib import import_module
from status import info, success


class YouTubeService(BaseProviderService):
    """
    Service class for YouTube automation.

    This should contain the actual YouTube-specific logic such as:
    - browser/session startup
    - content generation
    - metadata generation
    - upload flow
    - account-specific YouTube actions
    """

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        firefox_profile_path: str,
        niche: str,
    ) -> None:
        """
        Initialise the YouTube service.

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
        success("YouTube service started successfully.")
        info(f"UUID: {self.account_uuid}", False)
        info(f"Nickname: {self.account_nickname}", False)
        info(f"Niche: {self.niche}", False)
        info(f"Firefox Profile: {self.firefox_profile_path}", False)

    def generate_video(self) -> None:
        """
        Stub for future video generation logic.
        """
        load_and_render_prompt = import_module("prompt_loader").load_and_render_prompt
        prompt = load_and_render_prompt(
            prompt_name="generate_video",
            provider="youtube",
            provider_name="YouTube",
            account_nickname=self.account_nickname,
            niche=self.niche,
        )
        info("Loaded LM prompt template for YouTube.")
        info(prompt, False)
        info("generate_video() is not implemented yet.")

    def upload_video(self) -> None:
        """
        Stub for future upload logic.
        """
        info("upload_video() is not implemented yet.")