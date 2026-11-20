"""Apply a curated demo results CSV to the loaded calls.

    uv run apply-demo-results ../sample/demo_48/results.csv [--rules-dir ../docs/procedures/schema3]

Outer edge only: reads the files, opens one async session, and runs the ApplyDemoResults use case inside a
single transaction (commit on success, rollback on any error). Any bad row saves nothing. Uses DATABASE_URL.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.files.demo_results_files import read_results_csv, read_severity_bands
from app.adapters.persistence.demo_call_store import SqlAlchemyDemoCallStore
from app.adapters.persistence.engine import get_session
from app.application.apply_demo_results import ApplyDemoResults, ApplyOutcome
from app.domain.demo_results import ResultsRow, SeverityBand

DEFAULT_RULES = Path(__file__).resolve().parents[3] / "docs" / "procedures" / "schema3"

UseCaseRunner = Callable[[Sequence[ResultsRow], tuple[SeverityBand, ...]], Awaitable[ApplyOutcome]]


async def apply_with_session(
    session: AsyncSession, rows: Sequence[ResultsRow], bands: tuple[SeverityBand, ...]
) -> ApplyOutcome:
    """Run the use case as one unit of work on `session`."""
    async with session.begin():
        return await ApplyDemoResults(store=SqlAlchemyDemoCallStore(session), bands=bands).execute(rows)


async def _apply_with_database(
    rows: Sequence[ResultsRow],
    bands: tuple[SeverityBand, ...],
    session_source: Callable[[], AsyncIterator[AsyncSession]] = get_session,
) -> ApplyOutcome:
    """Take one session from `session_source` (default: engine.get_session), apply, then close the source."""
    source = session_source()
    session = await anext(source)
    try:
        return await apply_with_session(session, rows, bands)
    finally:
        await source.aclose()


def main(argv: Sequence[str] | None = None, run_use_case: UseCaseRunner | None = None) -> int:
    """Exit code 0 when every row was saved, 1 otherwise."""
    parser = argparse.ArgumentParser(prog="apply-demo-results", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("results_csv", type=Path)
    parser.add_argument("--rules-dir", type=Path, default=DEFAULT_RULES)
    args = parser.parse_args(argv)
    try:
        rows = read_results_csv(args.results_csv)
        bands = read_severity_bands(args.rules_dir)
    except (OSError, ValueError, KeyError) as error:
        print(f"error: {error}")
        return 1
    outcome = asyncio.run((run_use_case or _apply_with_database)(rows, bands))
    print(outcome.as_dict())
    return 0 if outcome.saved else 1


if __name__ == "__main__":
    raise SystemExit(main())
