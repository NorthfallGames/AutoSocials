import os
import sys
import json
from termcolor import colored

ROOT_DIR = os.path.dirname(sys.path[0])

def get_first_time_running() -> bool:
    """
    Checks if the program is running for the first time by checking if .as (.AutoSocials) folder exists.

    Returns:
        exists (bool): True if the program is running for the first time, False otherwise
    """
    return not os.path.exists(os.path.join(ROOT_DIR, ".as"))

def assert_folder_structure() -> None:
    """
        Make sure that the necessary folder structure is present.

        Returns:
            None
        """
    # Create the .mp folder
    if not os.path.exists(os.path.join(ROOT_DIR, ".as")):
        if get_verbose():
            print(colored(f"=> Creating .as folder at {os.path.join(ROOT_DIR, '.as')}", "green"))
        os.makedirs(os.path.join(ROOT_DIR, ".as"))

def rem_temp_files() -> None:
    """
    Removes temporary files in the `.as` directory.

    Returns:
        None
    """
    # Path to the `.mp` directory
    mp_dir = os.path.join(ROOT_DIR, ".as")

    files = os.listdir(mp_dir)

    for file in files:
        if not file.endswith(".json"):
            os.remove(os.path.join(mp_dir, file))

def get_verbose() -> bool:
    """
    Gets the verbose flag from the config file.

    Returns:
        verbose (bool): The verbose flag
    """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file)["verbose"]

def get_tts_voice_file() -> str:
    """
        Gets the configured TTS Voice.

        Returns:
            File location (str): The file location of the TTS voice
        """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file).get("tts_details", {}).get("tts_voice_file").strip().lower()

def get_tts_device() -> str:
    """
        Gets the configured TTS device.

        Returns:
            CPU or Cuda (str): The device to run TTS on
        """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file).get("tts_details", {}).get("tts_device", "cpu").strip().lower()

def get_script_sentence_length() -> int:
    """
    Gets the forced script's sentence length.
    Returns 4 if not set or invalid.

    Returns:
        int: Length of script sentences
    """
    try:
        with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
            config_json = json.load(file)
        value = config_json.get("youtube_details", {}).get("script_sentence_length", 4)
        return int(value)
    except (ValueError, TypeError):
        # If conversion fails (e.g. "abc"), fallback
        return 4

# Fix all the below
def get_llm_provider() -> str:
    """
    Gets the configured LLM provider.

    Returns:
        provider (str): "ollama" (default), "openrouter" or "LM Studio"
    """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file).get("llm_provider", "ollama").strip().lower()

def get_openrouter_api_key() -> str:
    """
    Gets the OpenRouter API key from config or environment variable.

    Returns:
        key (str): The OpenRouter API key
    """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        configured = json.load(file).get("openrouter_api_key", "")
        return configured or os.environ.get("OPENROUTER_API_KEY", "")

def get_default_model() -> str:
    """
    Gets the OpenRouter model name from the config file.

    Returns:
        model (str): The OpenRouter model name
    """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file).get("default_model", "openai/gpt-4o-mini")

def get_openai_endpoint() -> str:
    """
        Gets the custom LLM Endpoint from the config file.

        Returns:
            LM Endpoint (str): The openai compatible endpoint
        """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file).get("llm_endpoint", "http://127.0.0.1:1234/v1")

def get_ollama_base_url() -> str:
    """
    Gets the base URL for the local Ollama server.

    Returns:
        url (str): The base URL for the local Ollama server
    """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file).get("ollama_base_url", "http://127.0.0.1:1234")

def get_firefox_profile_path() -> str:
    """
    Gets the path to the Firefox profile.

    Returns:
        path (str): The path to the Firefox profile
    """
    with open(os.path.join(ROOT_DIR, "config.json"), "r") as file:
        return json.load(file)["firefox_profile"]