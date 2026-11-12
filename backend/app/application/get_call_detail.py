"""GetCallDetail use case: one stored call, assembled for the call detail screen. Depends on the domain and ports only.

It reads; it never analyzes a call or writes anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import CallDetailReader
from app.domain.call_detail import CallDetail, CallNotFound, build_call_detail


@dataclass(frozen=True)
class GetCallDetail:
    reader: CallDetailReader

    async def execute(self, call_id: int) -> CallDetail:
        record = await self.reader.get(call_id)
        if record is None:
            raise CallNotFound(call_id)
        return build_call_detail(record)
