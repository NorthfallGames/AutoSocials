import os
import torchaudio
import perth

from chatterbox.tts_turbo import ChatterboxTurboTTS
from config import get_tts_voice_file, get_tts_device, ROOT_DIR

class TTS:
    def __init__(self) -> None:
        self.tts_voice_file = get_tts_voice_file()
        self.tts_device = get_tts_device()
        self.output_path = os.path.join(ROOT_DIR, "output", "test.wav")

        if getattr(perth, "PerthImplicitWatermarker", None) is None:
            print("Perth watermarker unavailable, falling back to DummyWatermarker.")
            perth.PerthImplicitWatermarker = perth.DummyWatermarker

    def generate_test_audio(self) -> None:
        text = """
[happy] Hey there! This is a cheerful voice.
[sad] ...but sometimes things feel a bit down.
[angry] And occasionally, things get frustrating!
"""

        voice_file_path = os.path.join(ROOT_DIR, self.tts_voice_file)
        if not os.path.exists(voice_file_path):
            raise FileNotFoundError(f"Voice file not found: {voice_file_path}")

        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        tts = ChatterboxTurboTTS.from_pretrained(device=self.tts_device)

        audio = tts.generate(
            text=text,
            audio_prompt_path=str(voice_file_path)
        )

        # Chatterbox typically returns a torch tensor, not ready-made WAV bytes
        if hasattr(audio, "dim"):
            if audio.dim() == 1:
                audio = audio.unsqueeze(0)

            torchaudio.save(self.output_path, audio.cpu(), 24000)
        else:
            raise TypeError(f"Unexpected audio output type: {type(audio)}")

        print(f"Audio saved to: {self.output_path}")