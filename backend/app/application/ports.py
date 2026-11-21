"""Application ports for use cases."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.domain.call_analysis import CallToAnalyze
    from app.domain.call_detail import CallRecord as CallDetailRecord
    from app.domain.call_list import CallRecord, CallWindow, ListFilter, WeekTotals
    from app.domain.demo_results import ScoredCall, StoredCall
    from app.domain.ordered_evaluation import CallForEvaluation, EvaluatedStep, RequiredStep, StepDecision


class DatabaseProbe(Protocol):
    """Reports whether the application database accepts a connection."""

    async def ping(self) -> None:
        """Raise if the database cannot be reached."""


class DemoCallStore(Protocol):
    """Loads stored calls and saves their rescored results.

    save_results writes inside the caller's unit of work; the caller commits or rolls back.
    """

    async def find_calls(self, external_ids: Collection[str]) -> Mapping[str, StoredCall]:
        """Stored calls keyed by external id. Ids with no call are absent."""

    async def find_turns(self, external_ids: Collection[str]) -> Mapping[str, Mapping[int, str]]:
        """Each listed call's stored turns as idx -> text. Calls with no turns are absent."""

    async def save_results(self, calls: Sequence[ScoredCall]) -> None:
        """Write the new step results (with their evidence) and call totals."""


class Clock(Protocol):
    """The reference instant for "now"."""

    def now(self) -> datetime:
        """An aware datetime."""


class CallListReader(Protocol):
    """Reads what the calls list needs."""

    async def recent_calls(self, window: CallWindow, filters: ListFilter, limit: int) -> Sequence[CallRecord]:
        """Calls in the window that pass the filters, newest first, each with its steps in step order."""

    async def count_calls(self, window: CallWindow) -> int:
        """Number of calls in the window."""

    async def week_totals(self, window: CallWindow) -> Sequence[WeekTotals]:
        """Steps completed and total per UTC Monday-start week in the window, oldest week first."""


class RulesUnavailable(Exception):
    """The shared rules file could not be found."""

    def __init__(self, path: str) -> None:
        super().__init__(f"missing rules file: {path} (set RULES_DIR)")
        self.path = path


class ModelUnavailable(Exception):
    """The configured decision model could not give an answer."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"could not get a decision-model answer: {reason}")
        self.reason = reason


class CallAnalysisSource(Protocol):
    """Loads what analyzing one call needs."""

    async def load(self, call_id: int) -> CallToAnalyze | None:
        """The call with its procedure rules, or None when there is no such call."""

    async def turns(self, call_id: int) -> list[tuple[str, str]]:
        """The call's stored (speaker, text) turns in turn order."""


class PromptTemplateSource(Protocol):
    async def load(self) -> dict:
        """The shared prompt template and field types. Raises RulesUnavailable."""


class LanguageModel(Protocol):
    async def ask(self, prompt: str, model: str | None) -> tuple[str, str]:
        """(model name, answer text). Raises ModelUnavailable."""


class CallDetailReader(Protocol):
    """Reads one stored call with its turns and step results. Read only."""

    async def get(self, call_id: int) -> CallDetailRecord | None:
        """The call with this id, or None when no call has it."""


class OrderedCallStore(Protocol):
    """Loads and atomically saves one complete ordered-call evaluation."""

    async def load_for_evaluation(self, call_id: int) -> CallForEvaluation | None:
        """Return the stored call, procedure steps, and transcript evidence text."""

    async def save_evaluation(self, call: CallForEvaluation, steps: tuple[EvaluatedStep, ...]) -> None:
        """Persist all evaluated steps and recomputed call aggregates in the caller's transaction."""


class StepDecisionModel(Protocol):
    """Returns extracted facts for one required procedure step; it never decides stored status."""

    async def decide(self, call: CallForEvaluation, step: RequiredStep) -> StepDecision:
        """Return a structured observation, or raise ModelUnavailable."""


class OrderedCallSelector(Protocol):
    """Finds stored, complete calls for the offline evaluator command."""

    async def eligible_call_ids(self, call_type: str | None = None) -> tuple[int, ...]:
        """Return pending/scored call ids, optionally restricted to an assigned call type."""
