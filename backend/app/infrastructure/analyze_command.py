"""Composition root for `uv run analyze`; it is deliberately outside the use case."""

from __future__ import annotations

import argparse
import asyncio
import os
from collections.abc import Sequence

from app.adapters.command.analyze import AnalyzePresenter, evaluate_one
from app.adapters.llm.openai_decision import OpenAIDecisionModel
from app.adapters.persistence.engine import get_session
from app.adapters.persistence.ordered_call_store import SqlAlchemyOrderedCallStore
from app.application.evaluate_ordered_call.interactor import EvaluateOrderedCallInteractor
from app.application.ports import ModelUnavailable


def parse_args(argv: Sequence[str] | None = None):
    parser = argparse.ArgumentParser(prog="analyze", description="Evaluate completed calls with OpenAI Decisions.")
    selectors = parser.add_mutually_exclusive_group(required=True)
    selectors.add_argument("--call-id", type=int)
    selectors.add_argument("--call-type")
    selectors.add_argument("--all", action="store_true")
    return parser.parse_args(argv)


async def _run(args) -> list[dict[str, int]]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is required for analyze")
    source = get_session()
    session = await anext(source)
    try:
        store = SqlAlchemyOrderedCallStore(session)
        if args.call_id is not None:
            call_ids = (args.call_id,)
        else:
            call_ids = await store.eligible_call_ids(args.call_type)
            # SQLAlchemy opens a read transaction for the selector query. End it before
            # beginning the independent all-or-nothing transaction for each call.
            await session.rollback()
        model = OpenAIDecisionModel(api_key, os.environ.get("OPENAI_BASE_URL", "https://api.openai.com"))
        presenter = AnalyzePresenter()
        outputs: list[dict[str, int]] = []
        for call_id in call_ids:
            async with session.begin():
                output = await evaluate_one(EvaluateOrderedCallInteractor(store, model, presenter), call_id)
                outputs.append(presenter.as_dict(output))
        return outputs
    finally:
        await source.aclose()


def main(argv: Sequence[str] | None = None) -> int:
    try:
        outputs = asyncio.run(_run(parse_args(argv)))
    except (LookupError, ModelUnavailable, ValueError) as error:
        print(f"error: {error}")
        return 1
    for output in outputs:
        print(output)
    print({"saved": len(outputs)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
