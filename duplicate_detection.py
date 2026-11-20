"""Conservative duplicate candidate detection for administrator review."""
from __future__ import annotations

from difflib import SequenceMatcher

from database import get_complaints


def normalise(value: str) -> str:
    return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def find_possible_duplicate(category: str, location: str, description: str) -> tuple[bool, str | None]:
    target_location = normalise(location)
    target_description = normalise(description)
    for complaint in get_complaints(category=category):
        location_match = target_location == normalise(complaint["location"])
        description_match = SequenceMatcher(None, target_description, normalise(complaint["description"])).ratio() >= 0.65
        if location_match and description_match:
            return True, complaint["complaint_id"]
    return False, None
