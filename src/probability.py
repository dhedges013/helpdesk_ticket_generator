"""Probability profile utilities for weighted random selections."""

from __future__ import annotations

import csv
import json
import logging
import os
import random
from dataclasses import dataclass, field
from typing import Dict, Optional, Sequence, List

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


def _load_tech_names(path: str) -> List[str]:
    """Load technician names from the configured CSV file."""

    try:
        with open(path, "r", newline="", encoding="utf-8") as source:
            reader = csv.reader(source)
            techs = [row[0].strip() for row in reader if row and row[0].strip()]
    except FileNotFoundError:
        logger.warning("Tech CSV %s not found. No tech profiles will be assigned.", path)
        return []
    except Exception as exc:
        logger.error("Failed to load techs from %s: %s", path, exc)
        return []

    if not techs:
        logger.warning("Tech CSV %s is empty. No tech profiles will be assigned.", path)

    return techs


@dataclass(frozen=True)
class ProbabilityProfile:
    """Collection of weighting rules grouped by category plus closure heuristics."""

    name: str
    weights: Dict[str, Dict[str, float]] = field(default_factory=dict)
    same_day_close_rate: float = 0.25
    daily_close_rate: float = 0.15
    max_close_days: int = 14

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
        self._tech_profiles: Dict[str, str] = self._build_tech_profiles()
        self._customer_profiles: Dict[str, str] = self._coerce_mapping("customer_profiles")

    def _build_profiles(self, payload: object) -> Dict[str, ProbabilityProfile]:
        if not isinstance(payload, dict):
            payload = {}

        profiles: Dict[str, ProbabilityProfile] = {}
        for name, data in payload.items():
            if not isinstance(name, str):
                continue
            if not isinstance(data, dict):
                data = {}

            same_day_rate = float(data.get("same_day_close_rate", 0.25))
            daily_rate = float(data.get("daily_close_rate", 0.15))
            max_close_days = int(data.get("max_close_days", 14))

            weight_categories = {
                key: value
                for key, value in data.items()
                if isinstance(value, dict) and key not in {"close", "close_config"}
            }

            profiles[name] = ProbabilityProfile(
                name=name,
                weights=weight_categories,
                same_day_close_rate=max(0.0, min(1.0, same_day_rate)),
                daily_close_rate=max(0.0, min(1.0, daily_rate)),
                max_close_days=max(1, max_close_days),
            )

        if not profiles:
            profiles["default"] = ProbabilityProfile(name="default", weights={})

        return profiles

    def _assign_dynamic_tech_profiles(self) -> Dict[str, str]:
        """Assign each tech a random profile for the current run."""

        techs = _load_tech_names(config.TICKET_TECH)
        if not techs:
            return {}

        if not self._profiles:
            logger.warning("No profiles available to assign to technicians.")
            return {}

        profile_names = list(self._profiles.keys())
        assignments = {
            tech: random.choice(profile_names)
            for tech in techs
        }
        logger.info("Dynamically assigned probability profiles to %s technicians.", len(assignments))
        logger.debug("Tech profile assignments: %s", assignments)
        return assignments

    def _build_tech_profiles(self) -> Dict[str, str]:
        """Build tech profile mappings, preferring dynamic assignments."""

        dynamic_assignments = self._assign_dynamic_tech_profiles()
        if dynamic_assignments:
            return dynamic_assignments

        fallback_profiles = self._coerce_mapping("tech_profiles")
        if fallback_profiles:
            logger.info("Using fallback configured tech profiles from %s.", self._path)
        return fallback_profiles

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
        """Resolve a profile with tech taking precedence over customer."""
        if tech:
            profile_name = self._tech_profiles.get(tech)
            if profile_name:
                return self.get_profile(profile_name)

        if customer:
            profile_name = self._customer_profiles.get(customer)
            if profile_name:
                return self.get_profile(profile_name)

        return self.get_profile(self._default_profile_name)

    def resolve_tech_profile(self, tech: Optional[str]) -> ProbabilityProfile:
        """Return the profile mapped to *tech*, or the default if none is mapped."""

        if tech:
            profile_name = self._tech_profiles.get(tech)
            if profile_name:
                return self.get_profile(profile_name)
        return self.get_profile(self._default_profile_name)

    def resolve_customer_profile(self, customer: Optional[str]) -> ProbabilityProfile:
        """Return the profile mapped to *customer*, or the default if none is mapped."""

        if customer:
            profile_name = self._customer_profiles.get(customer)
            if profile_name:
                return self.get_profile(profile_name)
        return self.get_profile(self._default_profile_name)

    def get_default_profile(self) -> ProbabilityProfile:
        """Expose the registry's default profile."""

        return self.get_profile(self._default_profile_name)

    def get_tech_profile_mapping(self) -> Dict[str, str]:
        """Return the current tech-to-profile assignments."""

        return dict(self._tech_profiles)


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
