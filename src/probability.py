"""Probability profile utilities for weighted random selections."""

from __future__ import annotations

import json
import logging
import os
import random
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence

from . import config

logger = config.get_logger(__name__)

PROFILES_FILE = os.path.join(os.path.dirname(__file__), "probability_profiles.json")


def _load_profile_payload(path: str) -> Dict[str, object]:
    try:
        with open(path, "r", encoding="utf-8") as source:
            data = json.load(source)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        logger.warning("Probability profile file %s not found. Using defaults.", path)
        return {}
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse probability profile file %s: %s", path, exc)
        return {}


@dataclass(frozen=True)
class ProbabilityProfile:
    """Collection of weighting rules grouped by category."""

    name: str
    weights: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def weight_for(self, category: str, value: str) -> float:
        category_rules = self.weights.get(category) or {}
        default_weight = category_rules.get("__default__", 1.0)
        return max(0.0, float(category_rules.get(value, default_weight)))

    def pick(self, category: str, options: Sequence[str]) -> Optional[str]:
        if not options:
            return None

        weights = [self.weight_for(category, option) for option in options]
        if not any(weight > 0 for weight in weights):
            return random.choice(list(options))

        try:
            return random.choices(list(options), weights=weights, k=1)[0]
        except ValueError:
            logging.debug("Falling back to uniform selection for category %s.", category)
            return random.choice(list(options))


class ProbabilityProfileRegistry:
    """Loads and serves profiles plus per-entity mappings."""

    def __init__(self, path: str = PROFILES_FILE):
        self._path = path
        self._raw = _load_profile_payload(path)
        self._profiles = self._build_profiles(self._raw.get("profiles", {}))
        self._default_profile_name = self._determine_default()
        self._tech_profiles: Dict[str, str] = self._coerce_mapping("tech_profiles")
        self._customer_profiles: Dict[str, str] = self._coerce_mapping("customer_profiles")

    def _build_profiles(self, payload: object) -> Dict[str, ProbabilityProfile]:
        if not isinstance(payload, dict):
            payload = {}

        profiles = {
            name: ProbabilityProfile(name=name, weights=(data or {}))
            for name, data in payload.items()
            if isinstance(name, str)
        }

        if not profiles:
            profiles["default"] = ProbabilityProfile(name="default", weights={})

        return profiles

    def _determine_default(self) -> str:
        configured_default = self._raw.get("default_profile")
        if isinstance(configured_default, str) and configured_default in self._profiles:
            return configured_default

        return next(iter(self._profiles.keys()))

    def _coerce_mapping(self, key: str) -> Dict[str, str]:
        mapping = self._raw.get(key)
        if not isinstance(mapping, dict):
            return {}

        coerced: Dict[str, str] = {}
        for entity, profile_name in mapping.items():
            if profile_name in self._profiles and isinstance(entity, str):
                coerced[entity] = profile_name
        return coerced

    def get_profile(self, name: Optional[str]) -> ProbabilityProfile:
        if name and name in self._profiles:
            return self._profiles[name]
        return self._profiles[self._default_profile_name]

    def resolve_profile(
        self,
        *,
        tech: Optional[str] = None,
        customer: Optional[str] = None,
    ) -> ProbabilityProfile:
        if tech:
            profile_name = self._tech_profiles.get(tech)
            if profile_name:
                return self.get_profile(profile_name)

        if customer:
            profile_name = self._customer_profiles.get(customer)
            if profile_name:
                return self.get_profile(profile_name)

        return self.get_profile(self._default_profile_name)


_REGISTRY: Optional[ProbabilityProfileRegistry] = None


def get_registry() -> ProbabilityProfileRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ProbabilityProfileRegistry()
    return _REGISTRY


__all__ = [
    "ProbabilityProfile",
    "ProbabilityProfileRegistry",
    "get_registry",
]
