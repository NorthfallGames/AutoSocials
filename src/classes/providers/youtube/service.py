from classes.providers.base_service import BaseProviderService
from status import error, info, success
from importlib import import_module

from Tts import TTS
from lm_provider import generate_text

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


    def generate_topic(self) -> str:
        """
        Generates a topic based on the YouTube Channel niche.

        Returns:
            topic (str): The generated topic.
        """
        info("Loading prompt:")
        load_and_render_prompt = import_module("prompt_loader").load_and_render_prompt
        prompt = load_and_render_prompt(
            prompt_name="generate_script",
            provider="youtube",
            provider_name="YouTube",
            niche=self.niche,
        )
        success(f"Prompt loaded successfully: {prompt} ")
        info("Generating topic using LLM...")

        # Get the response
        completion = generate_text(prompt)
        success(f"Topic generated successfully: {completion}")

        if not completion:
            error("Failed to generate Topic.")

        self.subject = completion

        return completion

    def generate_video(self) -> None:
        """
        Stub for future video generation logic.
        """
        """load_and_render_prompt = import_module("prompt_loader").load_and_render_prompt
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

        info("Testing the TTS")
        tts = TTS()
        tts.generate_test_audio()
        """

        self.generate_topic()


    def upload_video(self) -> None:
        """
        Stub for future upload logic.
        """
        info("upload_video() is not implemented yet.")



    def test_connection(self) -> None:
        """
        Stub method to verify the service is wired correctly.
        """
        success("YouTube service started successfully.")
        info(f"UUID: {self.account_uuid}", False)
        info(f"Nickname: {self.account_nickname}", False)
        info(f"Niche: {self.niche}", False)
        info(f"Firefox Profile: {self.firefox_profile_path}", False)