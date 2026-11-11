"""Strict currency parsing and conservative company identity normalization."""

import math
import re
import unicodedata


def money(text: str) -> float | None:
    text = unicodedata.normalize("NFKC", text).strip().replace("−", "-")
    text = re.sub(r"₹|\bINR\b|\bRs\.?", "", text, flags=re.I).strip()
    # Permit conventional western and Indian grouping, never arbitrary commas.
    number = r"(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+|[0-9]{1,2}(?:,[0-9]{2})*,[0-9]{3})(?:\.[0-9]+)?"
    if not re.fullmatch(r"[+-]?" + number, text):
        return None
    value = float(text.replace(",", ""))
    return value if math.isfinite(value) else None


def normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name).casefold()
    name = re.sub(r"(?<=\s)ipo\s*$", "", name).strip()
    name = re.sub(r"\bltd\.?\b", "limited", name)
    name = name.replace("&", " and ")
    name = "".join(
        c if c.isalnum() or unicodedata.category(c).startswith("M") else "-" for c in name
    )
    return re.sub("-+", "-", name).strip("-")
