"""SQLAlchemy persistence for the ordered evaluator.

The adapter owns SQL mapping only.  It neither opens a transaction nor commits;
the command controller wraps load/evaluate/save in one transaction.
"""

from __future__ import annotations

from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.call_parse import last_logged_actions
from app.domain.demo_results import DEFAULT_SEVERITY_BANDS, severity_for
from app.domain.ordered_evaluation import CallForEvaluation, EvaluatedStep, ProcedureCheck, RequiredStep
from app.models import Call, CallStep, CallTurn, Procedure


def required_steps(rules: dict) -> tuple[RequiredStep, ...]:
    """Map persisted schema3 rule rows to the evaluator's small domain record."""
    return tuple(
        RequiredStep(
            row["key"], int(row["points"]), row.get("name", ""), row.get("done_when", ""), tuple(row.get("logs", ())),
            any(check.get("type") in {"logged_task_type", "logged_matches_request"} for check in row.get("sub_checks", ())),
            tuple(ProcedureCheck(
                check["key"], check["type"], int(check["points"]), tuple(check.get("fields", ())), check.get("expected")
            ) for check in row.get("sub_checks", ())),
        )
        for row in rules.get("steps", ())
    )


def severity(points_lost: int) -> str:
    """Use the shared severity bands used by the demo-result scorer."""
    return severity_for(DEFAULT_SEVERITY_BANDS, points_lost)


class SqlAlchemyOrderedCallStore:
    """An `OrderedCallStore` over one caller-owned async session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def eligible_call_ids(
        self, call_type: str | None = None, call_id: int | None = None, include_existing: bool = False
    ) -> tuple[int, ...]:
        statuses = ("pending", "scored", "needs_review") if include_existing else ("pending",)
        query = select(Call.id).where(Call.status.in_(statuses)).order_by(Call.id)
        if call_type is not None:
            query = query.where(Call.call_type == call_type)
        if call_id is not None:
            query = query.where(Call.id == call_id)
        return tuple((await self._session.execute(query)).scalars())

    async def load_for_evaluation(self, call_id: int) -> CallForEvaluation | None:
        row = (await self._session.execute(
            select(Call.id, Call.raw_metadata, Procedure.rules).join(Procedure, Procedure.id == Call.procedure_id).where(Call.id == call_id)
        )).first()
        if row is None:
            return None
        turns = (await self._session.execute(
            select(CallTurn.idx, CallTurn.speaker, CallTurn.text).where(CallTurn.call_id == call_id).order_by(CallTurn.idx)
        )).all()
        return CallForEvaluation(
            id=row.id,
            steps=required_steps(row.rules),
            turn_texts={turn.idx: turn.text for turn in turns},
            agent_turn_indices=tuple(turn.idx for turn in turns if turn.speaker == "agent"),
            logged_actions=last_logged_actions(row.raw_metadata),
            # This offline command evaluates persisted, completed call records only.
            call_ended=True,
        )

    async def save_evaluation(self, evaluation: CallForEvaluation, steps: tuple[EvaluatedStep, ...]) -> None:
        call = await self._session.get(Call, evaluation.id)
        if call is None:
            raise LookupError(f"no call with id {evaluation.id}")
        if len(steps) != len(evaluation.steps):
            raise ValueError("an ended-call evaluation must contain every required procedure step")
        existing = {step.step_key: step for step in (await self._session.execute(
            select(CallStep).where(CallStep.call_id == evaluation.id)
        )).scalars()}
        for position, (required, result) in enumerate(zip(evaluation.steps, steps, strict=True), 1):
            if required.key != result.key:
                raise ValueError("evaluation result order does not match the stored procedure")
            step = existing.get(result.key)
            if step is None:
                step = CallStep(
                    call_id=evaluation.id, step_key=required.key, position=position,
                    name=required.name or required.key.replace("_", " ").title(), points=required.points,
                    status=result.status,
                )
                self._session.add(step)
            step.status = result.status
            step.points_lost = result.points_lost
            step.points_under_review = result.points_under_review
            step.severity = severity(result.points_lost)
            step.evidence_turn_idx = result.evidence.turn_idx if result.evidence else None
            step.evidence_quote = result.evidence.quote if result.evidence else None
            step.decision_confidence = result.decision_confidence
            step.decision_response = result.decision_response
            step.sub_checks = [
                {"key": outcome.key, "points_lost": outcome.points_lost, "under_review": outcome.under_review}
                for outcome in result.check_outcomes
            ]
        counts = Counter(step.status for step in steps)
        points_lost = sum(step.points_lost for step in steps)
        points_total = sum(step.points for step in evaluation.steps)
        call.steps_total = len(steps)
        call.steps_completed = counts["completed"]
        call.steps_missed = counts["missed"]
        call.steps_wrong = counts["wrong"]
        call.steps_under_review = counts["under_review"]
        call.points_lost = points_lost
        call.status = "needs_review" if counts["under_review"] else "scored"
        call.score = None if counts["under_review"] else round(100 * (points_total - points_lost) / points_total) if points_total else 100
