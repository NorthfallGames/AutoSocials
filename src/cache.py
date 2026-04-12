import os
import json

from typing import List
from config import ROOT_DIR
from constants import SUPPORTED_PROVIDERS

def get_cache_path() -> str:
    """
    Gets the path to the cache file.

    Returns:
        path (str): The path to the cache folder
    """
    return os.path.join(ROOT_DIR, '.as')

def get_social_cache_path(social: str) -> str:
    """
    Gets the cache file path for any social/provider.

    Args:
        social (str): Provider name (e.g. "twitter", "youtube", "linkedin")

    Returns:
        str: Full path to the provider cache file
    """
    return os.path.join(get_cache_path(), f"{social}.json")


def get_provider_cache_path(provider: str) -> str:
    """
    Gets the cache path for a supported account provider.

    Args:
        provider (str): The provider name

    Returns:
        str: The provider-specific cache path

    Raises:
        ValueError: If the provider is unsupported
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported provider '{provider}'. Expected one of: {', '.join(SUPPORTED_PROVIDERS)}"
        )

    return get_social_cache_path(provider)

def get_accounts(provider: str) -> List[dict]:
    """
    Gets the accounts from the cache.

    Args:
        provider (str): The provider to get the accounts for

    Returns:
        account (List[dict]): The accounts
    """
    cache_path = get_provider_cache_path(provider)

    if not os.path.exists(cache_path):
        # Create the cache file
        with open(cache_path, 'w') as file:
            json.dump({
                "accounts": []
            }, file, indent=4)

    with open(cache_path, 'r') as file:
        parsed = json.load(file)

        if parsed is None:
            return []

        if 'accounts' not in parsed:
            return []

        # Get accounts dictionary
        return parsed['accounts']

def add_account(provider: str, account: dict) -> None:
    """
    Adds an account to the cache.

    Args:
        provider (str): The provider to add the account to.
        account (dict): The account to add

    Returns:
        None
    """
    cache_path = get_provider_cache_path(provider)

    # Get the current accounts
    accounts = get_accounts(provider)

    # Add the new account
    accounts.append(account)

    # Write the new accounts to the cache
    with open(cache_path, 'w') as file:
        json.dump({
            "accounts": accounts
        }, file, indent=4)

def remove_account(provider: str, account_id: str) -> bool:
    """
    Removes an account from the cache by id.

    Args:
        provider (str): The provider to remove the account from.
        account_id (str): The account id to remove

    Returns:
        removed (bool): True if an account was removed, otherwise False
    """
    cache_path = get_provider_cache_path(provider)
    accounts = get_accounts(provider)

    original_length = len(accounts)
    accounts = [account for account in accounts if account.get("id") != account_id]

    with open(cache_path, 'w') as file:
        json.dump({
            "accounts": accounts
        }, file, indent=4)

    return len(accounts) != original_length
