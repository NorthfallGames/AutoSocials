"""
This file contains all the constants used in the program.
"""

TWITTER_TEXTAREA_CLASS = "public-DraftStyleDefault-block public-DraftStyleDefault-ltr"
TWITTER_POST_BUTTON_XPATH = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/div/div[2]/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div/div/div[3]"

OPTIONS = [
    "YouTube Shorts Automater",
    "Twitter Bot",
    "LinkedIn Bot",
    "Quit"
]

SUPPORTED_PROVIDERS = frozenset({
    "twitter",
    "youtube",
    "linkedin",
})

COMMON_ACCOUNT_FIELDS = [
    ("nickname", "a nickname for this account"),
    ("niche", "the account niche"),
]