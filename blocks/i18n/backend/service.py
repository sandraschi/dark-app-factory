"""Internationalization service — translations, locale management."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("dark_factory")

_translations: dict[str, dict[str, str]] = {}  # locale -> {key: translated}
_supported: list[str] = []


def configure():
    global _supported
    raw = os.environ.get("SUPPORTED_LOCALES", "en,de,fr,es,it")
    _supported = [x.strip() for x in raw.split(",") if x.strip()]


def get_supported() -> list[str]:
    if not _supported:
        configure()
    return _supported


def get_default() -> str:
    return os.environ.get("DEFAULT_LOCALE", "en")


def set_translation(locale: str, key: str, value: str) -> dict:
    if locale not in _translations:
        _translations[locale] = {}
    _translations[locale][key] = value
    return {"locale": locale, "key": key, "value": value}


def get_translations(locale: str) -> dict[str, str]:
    base = _translations.get(get_default(), {})
    overrides = _translations.get(locale, {})
    return {**base, **overrides}


def translate(key: str, locale: str, fallback: str = "") -> str:
    loc = _translations.get(locale, {})
    if key in loc:
        return loc[key]
    default = get_default()
    if locale != default:
        def_loc = _translations.get(default, {})
        if key in def_loc:
            return def_loc[key]
    return fallback or key


def bulk_import(locale: str, pairs: dict[str, str]) -> int:
    if locale not in _translations:
        _translations[locale] = {}
    count = 0
    for k, v in pairs.items():
        _translations[locale][k] = v
        count += 1
    return count
