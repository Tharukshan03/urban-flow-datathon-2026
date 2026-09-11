"""Intent routing for the mobility assistant."""

from __future__ import annotations

from dataclasses import dataclass

from .utils import (
    extract_horizon,
    extract_proper_noun_phrase,
    extract_time_bucket,
    extract_top_n,
    fuzzy_match,
    looks_ambiguous,
    normalize_text,
    unsupported_topic,
)


@dataclass(frozen=True)
class RoutedQuestion:
    kind: str
    question: str
    horizon_hours: int | None = None
    zone_name: str | None = None
    borough_name: str | None = None
    time_bucket: str | None = None
    top_n: int = 5
    suggestions: tuple[str, ...] = ()
    clarification: str | None = None
    unsupported_message: str | None = None


def _contains_any(text: str, values: tuple[str, ...]) -> bool:
    return any(value in text for value in values)


def _forecast_context(normal: str, horizon: int | None) -> bool:
    if horizon is None:
        return False
    if any(term in normal for term in ('forecast', 'planning', 'model', 'best', 'use', 'backtest', 'mae', 'rmse')):
        return True
    return normal.startswith('what about ') or normal.startswith('what is the') and 'hours' in normal


def route_question(question: str, catalog) -> RoutedQuestion:
    normal = normalize_text(question)
    horizon = extract_horizon(question)
    time_bucket = extract_time_bucket(question)
    top_n = extract_top_n(question)

    if not normal:
        return RoutedQuestion('clarify', question, clarification='Please ask about demand, routes, forecasts, boroughs or recommendations.')

    if unsupported_topic(question) and not _contains_any(normal, ('forecast', 'pickup', 'dropoff', 'route', 'borough', 'weekday', 'hour', 'recommend')):
        return RoutedQuestion(
            'unsupported',
            question,
            unsupported_message='This assistant supports demand, hotspots, OD flows, forecasts and operational recommendations, but not revenue, profit or next-month planning questions.',
        )

    zone_choices = getattr(catalog, 'zone_names', ()) or ()
    borough_choices = getattr(catalog, 'borough_names', ()) or ()
    zone_name, zone_suggestions = fuzzy_match(question, zone_choices) if zone_choices else (None, ())
    borough_name, borough_suggestions = fuzzy_match(question, borough_choices) if borough_choices else (None, ())

    proper_noun = extract_proper_noun_phrase(question)
    if proper_noun and zone_name is None and borough_name is None:
        _, proper_suggestions = fuzzy_match(proper_noun, zone_choices) if zone_choices else (None, ())
        return RoutedQuestion('unknown_zone', question, suggestions=proper_suggestions, clarification=f'I could not find a zone named {proper_noun}.')

    if horizon is not None and _forecast_context(normal, horizon):
        if zone_name:
            return RoutedQuestion('saved_forecast', question, horizon_hours=horizon, zone_name=zone_name)
        return RoutedQuestion('forecast_metrics', question, horizon_hours=horizon, top_n=top_n)

    if _contains_any(normal, ('forecast', 'outlook', 'prediction', 'plan for')) and zone_name:
        return RoutedQuestion('clarify', question, zone_name=zone_name, clarification=f'I found the zone {zone_name}, but I still need a horizon. Please ask for 24, 48, or 72 hours.')

    if _contains_any(normal, ('recommend', 'should fleet', 'what should', 'fleet manager', 'fleet managers', 'operational recommendation', 'do during')):
        return RoutedQuestion('recommendations', question)

    if _contains_any(normal, ('borough',)):
        return RoutedQuestion('borough_demand', question, borough_name=borough_name, top_n=top_n)

    if _contains_any(normal, ('weekday', 'week day', 'day of week')):
        return RoutedQuestion('weekday_demand', question, top_n=top_n)

    if _contains_any(normal, ('time of day', 'highest demand', 'when is demand highest', 'when demand highest', 'hourly', 'hour')) and not horizon:
        return RoutedQuestion('hourly_demand', question, top_n=top_n)

    if _contains_any(normal, ('destination', 'dropoff', 'dropped off')):
        return RoutedQuestion('top_destinations', question, top_n=top_n)

    if _contains_any(normal, ('pickup', 'busiest zones', 'hotspot', 'hotspots', 'busiest pickup', 'pickup zones')):
        return RoutedQuestion('top_pickups', question, top_n=top_n)

    if _contains_any(normal, ('route', 'od ', 'origin destination', 'origin-destination', 'usual go', 'usually go', 'where do trips from', 'strongest route', 'common route', 'pair')):
        if zone_name and _contains_any(normal, ('from ', 'origin', 'usually go', 'go to', 'where do trips from')):
            return RoutedQuestion('od_from_zone', question, zone_name=zone_name, time_bucket=time_bucket, top_n=top_n)
        if time_bucket:
            return RoutedQuestion('od_time', question, time_bucket=time_bucket, zone_name=zone_name, top_n=top_n)
        return RoutedQuestion('od_overall', question, zone_name=zone_name, top_n=top_n)

    if looks_ambiguous(question):
        return RoutedQuestion('clarify', question, clarification='Do you want historical hourly demand, a specific zone, a saved forecast, or an OD route?')

    return RoutedQuestion('unsupported', question, unsupported_message='I could not map that request to a supported mobility analytics intent.')
