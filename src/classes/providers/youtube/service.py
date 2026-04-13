from classes.providers.base_service import BaseProviderService
from importlib import import_module
import re
from typing import List
import json
import uuid

from status import error, info, success, warning
from prompt_loader import load_and_render_prompt
from config import *
from Tts import TTS
from lm_provider import generate_text
from comfyui import ComfyUI

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

    def __init__(self, account_uuid: str, account_nickname: str, firefox_profile_path: str, niche: str, ) -> None:
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

        self.comfy = ComfyUI()

    def generate_topic(self) -> str:
        """
        Generates a topic based on the YouTube Channel niche.

        Returns:
            topic (str): The generated topic.
        """
        info("Loading prompt:")
        prompt = load_and_render_prompt(
            prompt_name="generate_topic",
            provider="youtube",
            provider_name="YouTube",
            niche=self.niche,
        )
        if get_verbose():
            success(f"Prompt loaded successfully: {prompt} ")
        info("Generating topic using LLM...")

        # Get the response
        completion = generate_text(prompt)
        if get_verbose():
            success(f"Topic generated successfully: {completion}")

        if not completion:
            error("Failed to generate Topic.")

        self.subject = completion

        return completion

    def generate_script(self) -> str | None:
        """
        Generate a script for a video, depending on the subject of the video, the number of paragraphs, and the AI model.

        Returns:
            script (str): The script of the video.
        """
        sentence_length = get_script_sentence_length()
        info("Loading script generator:")
        prompt = load_and_render_prompt(
            prompt_name="generate_script",
            provider="youtube",
            provider_name="YouTube",
            sentence_length=sentence_length,
            subject=self.subject,
        )
        if get_verbose():
            success(f"Prompt loaded successfully: {prompt} ")
        info("Generating script using LLM...")

        completion = generate_text(prompt)
        if get_verbose():
            success(f"Script generated successfully: {completion}")

        # Apply regex to remove *
        completion = re.sub(r"\*", "", completion)

        if not completion:
            error("The generated script is empty.")

        if len(completion) > 5000:
            warning("Generated Script is too long. Retrying...")
            return self.generate_script()

        self.script = completion

        return completion

    def generate_metadata(self) -> dict:
        """
        Generates Video metadata for the to-be-uploaded YouTube Short (Title, Description).

        Returns:
            metadata (dict): The generated metadata.
        """

        info("Loading Title generator:")
        prompt = load_and_render_prompt(
            prompt_name="generate_title",
            provider="youtube",
            provider_name="YouTube",
            subject=self.subject,
        )
        if get_verbose():
            success(f"Prompt loaded successfully: {prompt} ")

        # Generate the title
        title = generate_text(prompt)
        if get_verbose():
            success(f"Title generated successfully: {title}")

        #### Self care prompt - to do before retrying title generation
        if len(title) > 100:
            if get_verbose():
                warning("Generated Title is too long. Retrying...")
            return self.generate_metadata()

        # Generate the description
        info("Loading Title generator:")
        prompt = load_and_render_prompt(
            prompt_name="generate_description",
            provider="youtube",
            provider_name="YouTube",
            script=self.script,
        )
        if get_verbose():
            success(f"Prompt loaded successfully: {prompt} ")

        description =generate_text(prompt)
        if get_verbose():
            success(f"Description generated successfully: {description}")

        self.metadata = {"title": title, "description": description}

        return self.metadata

        self.metadata = {"title": title, "description": description}

        return self.metadata

    def generate_prompts(self) -> list[str]:
        n_prompts = max(1, int(len(self.script) / 3))

        info("Loading Title generator:")
        prompt = load_and_render_prompt(
            prompt_name="generate_prompts",
            provider="youtube",
            provider_name="YouTube",
            n_prompts=n_prompts,
            subject=self.subject,
            script=self.script
        )

        completion = (
            str(generate_text(prompt) or "")
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        image_prompts = []

        try:
            parsed = json.loads(completion)

            if isinstance(parsed, dict) and "image_prompts" in parsed:
                image_prompts = parsed["image_prompts"]
            elif isinstance(parsed, list):
                image_prompts = parsed
            else:
                raise ValueError("Prompt response was not a dict or list")

        except Exception:
            warning("LLM returned an unformatted response. Attempting to clean...")

            match = re.search(r"\[.*\]", completion, re.DOTALL)
            if not match:
                warning("Failed to generate Image Prompts. Retrying...")
                return self.generate_prompts()

            try:
                image_prompts = json.loads(match.group(0))
            except Exception:
                warning("Failed to parse cleaned image prompt list. Retrying...")
                return self.generate_prompts()

        image_prompts = [
            p.strip()
            for p in image_prompts
            if isinstance(p, str) and p.strip()
        ]

        if len(image_prompts) > n_prompts:
            image_prompts = image_prompts[:n_prompts]

        if not image_prompts:
            warning("No valid image prompts were produced. Retrying...")
            return self.generate_prompts()

        self.image_prompts = image_prompts

        success(f"Generated {len(image_prompts)} Image Prompts.")
        return image_prompts

    def generate_image(self, prompt: str) -> str:
        """
        Generates an AI Image based on the given prompt using Nano Banana 2.

        Args:
            prompt (str): Reference for image generation

        Returns:
            path (str): The path to the generated image.
        """
        return self.comfy.generate_image(prompt)

    def generate_script_to_speech(self) -> str:
        """
        Converts the generated script into Speech using Chatterbox and returns the path to the wav file.

        Args:
            tts_instance (tts): Instance of TTS Class.

        Returns:
            path_to_wav (str): Path to generated audio (WAV Format).
        """
        path = os.path.join(ROOT_DIR, "output", "audio", str(uuid.uuid4()) + ".wav")

        # Clean script, remove every character that is not a word character, a space, a period, a question mark, or an exclamation mark.
        self.script = re.sub(r"[^\w\s.?!]", "", self.script)

        tts = TTS()
        tts.generate_test_audio(self.script, path)

        self.tts_path = path

        if get_verbose():
            info(f' => Wrote TTS to "{path}"')

        return path

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
        self.generate_script()
        self.generate_metadata()
        self.generate_prompts()

        for prompt in self.image_prompts:
            self.generate_image(prompt)

        # @TODO Need to test this function to make sure that it works
        self.generate_script_to_speech()


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