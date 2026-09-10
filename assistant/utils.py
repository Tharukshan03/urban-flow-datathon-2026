"""Shared helpers for the mobility assistant."""

from __future__ import annotations

from difflib import get_close_matches
from pathlib import Path
import re
from typing import Iterable

DATA_DIR = Path(__file__).resolve().parent / 'data'

UNSUPPORTED_WORDS = {
    'revenue', 'profit', 'loss', 'margin', 'cost', 'savings', 'budget', 'salary',
    'roi', 'investment'
}


def normalize_text(text: str) -> str:
    lowered = text.strip().lower()
    lowered = lowered.replace('morning rush', 'morning peak')
    lowered = lowered.replace('evening rush', 'evening peak')
    lowered = lowered.replace('pickup area', 'pickup zone')
    lowered = lowered.replace('dropoff area', 'dropoff zone')
    lowered = re.sub(r'[^a-z0-9\s\-:/]', ' ', lowered)
    return re.sub(r'\s+', ' ', lowered).strip()


def extract_top_n(text: str, default: int = 5) -> int:
    match = re.search(r'\btop\s+(\d+)\b', text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else default


def extract_horizon(text: str) -> int | None:
    normal = normalize_text(text)
    if '24' in normal and any(term in normal for term in ('forecast', 'planning', 'model', 'best', 'use', 'next day', 'next-day', 'hours')):
        return 24
    if '48' in normal and any(term in normal for term in ('forecast', 'planning', 'model', 'best', 'use', 'hours')):
        return 48
    if '72' in normal and any(term in normal for term in ('forecast', 'planning', 'model', 'best', 'use', 'hours')):
        return 72
    if 'next day' in normal or 'next-day' in normal:
        return 24
    if '2 day' in normal or 'two day' in normal or '2-day' in normal:
        return 48
    if '3 day' in normal or 'three day' in normal or '3-day' in normal:
        return 72
    return None


def extract_time_bucket(text: str) -> str | None:
    normal = normalize_text(text)
    if any(term in normal for term in ('morning peak', 'morning rush', 'morning', 'am peak')):
        return 'morning_peak'
    if any(term in normal for term in ('midday', 'noon', 'lunch')):
        return 'midday'
    if any(term in normal for term in ('evening peak', 'evening rush', 'evening', 'pm peak')):
        return 'evening_peak'
    if any(term in normal for term in ('late night', 'overnight', 'night', 'nighttime', 'after hours')):
        return 'late_night'
    return None


def direct_name_match(text: str, choices: Iterable[str]) -> str | None:
    normal = normalize_text(text)
    for choice in choices:
        if normalize_text(choice) in normal:
            return choice
    return None


def fuzzy_match(text: str, choices: Iterable[str]) -> tuple[str | None, tuple[str, ...]]:
    items = tuple(dict.fromkeys(choices))
    direct = direct_name_match(text, items)
    if direct:
        return direct, ()
    normal = normalize_text(text)
    matches = get_close_matches(normal, [normalize_text(choice) for choice in items], n=5, cutoff=0.72)
    if not matches:
        return None, ()
    recovered = []
    for match in matches:
        for choice in items:
            if normalize_text(choice) == match:
                recovered.append(choice)
                break
    return (recovered[0] if recovered else None), tuple(recovered)


def join_phrases(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    if not values:
        return ''
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f'{values[0]} and {values[1]}'
    return ', '.join(values[:-1]) + f', and {values[-1]}'


def looks_ambiguous(text: str) -> bool:
    normal = normalize_text(text)
    if not normal:
        return True
    vague = {'how busy is it', 'how busy', 'how is it', 'how are things', 'how is demand', 'how bad is it'}
    if any(phrase in normal for phrase in vague):
        return True
    broad_terms = {'busy', 'demand', 'traffic', 'congestion', 'volume'}
    has_broad = any(term in normal for term in broad_terms)
    has_specific = any(token in normal for token in ('zone', 'borough', 'hour', 'weekday', 'forecast', 'route', 'od', 'evening', 'morning', 'night', 'jfk', 'upper east', 'midtown', 'manhattan'))
    return has_broad and not has_specific


def unsupported_topic(text: str) -> bool:
    normal = normalize_text(text)
    return any(term in normal for term in UNSUPPORTED_WORDS)


def extract_proper_noun_phrase(text: str) -> str | None:
    match = re.search(r'\b(?:in|for|at|from|to)\s+([A-Z][\w\'\-]*(?:\s+[A-Z][\w\'\-]*){0,4})', text)
    if match:
        return match.group(1).strip()
    return None
