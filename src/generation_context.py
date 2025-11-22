"""Shared context passed between generation steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING, List

from . import config
from .probability import ProbabilityProfile, ProbabilityProfileRegistry, get_registry

if TYPE_CHECKING:  # pragma: no cover
    from .validators import ValidatorPipeline


@dataclass
class GenerationContext:
    probability_registry: ProbabilityProfileRegistry = field(default_factory=get_registry)
    validator_pipeline: Optional["ValidatorPipeline"] = None

    def __post_init__(self) -> None:
        if self.validator_pipeline is None:
            from .validators import ValidatorPipeline

            self.validator_pipeline = ValidatorPipeline(
                daily_ticket_cap=config.DAILY_TICKET_CAP,
                time_entry_buffer_minutes=config.TIME_ENTRY_BUFFER_MINUTES,
            )

    def resolve_profile(self, *, tech: Optional[str] = None, customer: Optional[str] = None) -> ProbabilityProfile:
        return self.probability_registry.resolve_profile(tech=tech, customer=customer)

    def resolve_tech_profile(self, tech: Optional[str]) -> ProbabilityProfile:
        return self.probability_registry.resolve_tech_profile(tech)

    def resolve_customer_profile(self, customer: Optional[str]) -> ProbabilityProfile:
        return self.probability_registry.resolve_customer_profile(customer)

    def validate_ticket(self, ticket: dict) -> dict:
        if self.validator_pipeline:
            return self.validator_pipeline.validate_ticket(ticket)
        return ticket

    def validate_time_entries(self, ticket: dict, entries: Optional[List[dict]]) -> List[dict]:
        normalized_entries = entries or []
        if self.validator_pipeline:
            return self.validator_pipeline.validate_time_entries(ticket, normalized_entries)
        return normalized_entries
