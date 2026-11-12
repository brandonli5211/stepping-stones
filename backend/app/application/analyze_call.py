"""AnalyzeCall use case. Depends on the domain and ports only."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.ports import CallAnalysisSource, LanguageModel, PromptTemplateSource
from app.domain.call_analysis import (
    CallNotFound,
    ModelAnalysis,
    NoTranscript,
    PromptPreview,
    agent_name_from_metadata,
    build_prompt,
    clean_answer,
    parse_answer,
    transcript_from_turns,
)


@dataclass(frozen=True)
class AnalyzeCall:
    """Build the coaching prompt for one call; return it (dry run) or the model's cleaned, parsed answer."""

    calls: CallAnalysisSource
    template: PromptTemplateSource
    model: LanguageModel

    async def execute(self, call_id: int, model_name: str | None = None, dry_run: bool = False) -> PromptPreview | ModelAnalysis:
        call = await self.calls.load(call_id)
        if call is None:
            raise CallNotFound(call_id)
        transcript = call.raw_transcript
        if not transcript:  # calls loaded before raw_transcript existed: rebuild from the turns
            transcript = transcript_from_turns(await self.calls.turns(call.id))
        if not transcript:
            raise NoTranscript(call_id)

        common = await self.template.load()
        prompt = build_prompt(common, call.rules, transcript, agent_name_from_metadata(call.metadata))
        if dry_run:
            return PromptPreview(id=call.id, external_id=call.external_id, call_type=call.call_type, prompt=prompt)

        name, answer = await self.model.ask(prompt, model_name)
        raw = clean_answer(answer)
        return ModelAnalysis(id=call.id, external_id=call.external_id, call_type=call.call_type, model=name,
                             result=parse_answer(raw), raw=raw)
