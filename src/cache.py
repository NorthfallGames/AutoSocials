import json
import os
import re
from typing import List

from config import ROOT_DIR


_PROVIDER_SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def get_cache_path() -> str:
    """
    Gets the path to the cache folder.

    Returns:
        str: The path to the cache folder
    """
    return os.path.join(ROOT_DIR, ".as")


def validate_provider_name(provider: str) -> str:
    """
    Validates that the provider name is safe to use as a cache filename.

    Args:
        provider (str): Provider slug such as "youtube" or "facebook"

    Returns:
        str: The validated provider slug

    Raises:
        ValueError: If the provider slug is invalid
    """
    if not isinstance(provider, str):
        raise ValueError("Provider name must be a string.")

    provider = provider.strip().lower()

    if not provider:
        raise ValueError("Provider name cannot be empty.")

    if not _PROVIDER_SLUG_PATTERN.fullmatch(provider):
        raise ValueError(
            "Invalid provider name. Expected slug format like "
            "'youtube', 'linkedin', or 'tiktok_bot'."
        )

    return provider


def get_social_cache_path(social: str) -> str:
    """
    Gets the cache file path for any social/provider.

    Args:
        social (str): Provider name (e.g. "twitter", "youtube", "linkedin")

    Returns:
        str: Full path to the provider cache file
    """
    social = validate_provider_name(social)
    return os.path.join(get_cache_path(), f"{social}.json")


def get_provider_cache_path(provider: str) -> str:
    """
    Gets the cache path for a provider.

    Args:
        provider (str): The provider name

    Returns:
        str: The provider-specific cache path
    """
    return get_social_cache_path(provider)


def ensure_cache_file(provider: str) -> str:
    """
    Ensures the provider cache file exists.

    Args:
        provider (str): Provider name

    Returns:
        str: Path to the provider cache file
    """
    cache_dir = get_cache_path()
    os.makedirs(cache_dir, exist_ok=True)

    cache_path = get_provider_cache_path(provider)

    if not os.path.exists(cache_path):
        with open(cache_path, "w", encoding="utf-8") as file:
            json.dump({"accounts": []}, file, indent=4)

    return cache_path


def get_accounts(provider: str) -> List[dict]:
    """
    Gets the accounts from the cache.

    Args:
        provider (str): The provider to get the accounts for

    Returns:
        List[dict]: The accounts
    """
    cache_path = ensure_cache_file(provider)

    with open(cache_path, "r", encoding="utf-8") as file:
        parsed = json.load(file)

    if not parsed:
        return []

    if "accounts" not in parsed:
        return []

    accounts = parsed["accounts"]
    if not isinstance(accounts, list):
        return []

    return accounts


def add_account(provider: str, account: dict) -> None:
    """
    Adds an account to the cache.

    Args:
        provider (str): The provider to add the account to
        account (dict): The account to add
    """
    cache_path = ensure_cache_file(provider)
    accounts = get_accounts(provider)
    accounts.append(account)

    with open(cache_path, "w", encoding="utf-8") as file:
        json.dump({"accounts": accounts}, file, indent=4)


def remove_account(provider: str, account_id: str) -> bool:
    """
    Removes an account from the cache by id.

    Args:
        provider (str): The provider to remove the account from
        account_id (str): The account id to remove

    Returns:
        bool: True if an account was removed, otherwise False
    """
    cache_path = ensure_cache_file(provider)
    accounts = get_accounts(provider)

    original_length = len(accounts)
    accounts = [account for account in accounts if account.get("id") != account_id]

    with open(cache_path, "w", encoding="utf-8") as file:
        json.dump({"accounts": accounts}, file, indent=4)

    return len(accounts) != original_length