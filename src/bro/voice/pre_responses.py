"""Acoustic pre-response filler sentences for Bro.

Fills the silence while the LLM processes queries in audio mode.
"""

import random
from typing import List

PRE_RESPONSES: List[str] = [
    "Okay, analyzing your request.",
    "Surely, I'm checking that out.",
    "Right away, looking into this now.",
    "On it, processing your request.",
    "Understood, give me just a moment.",
    "Working on it, analyzing the data.",
    "Certainly, let me handle that for you.",
    "Checking on that right now, sir.",
    "Processing your command, one moment.",
    "Analyzing your request, standing by.",
]

def get_random_pre_response() -> str:
    """Return a randomized pre-response acknowledgment phrase."""
    return random.choice(PRE_RESPONSES)
