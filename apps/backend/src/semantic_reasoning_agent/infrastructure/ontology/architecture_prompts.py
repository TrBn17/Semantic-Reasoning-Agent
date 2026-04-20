from __future__ import annotations

from collections.abc import Sequence


_ARCHITECT_PROMPT = """You are designing an ontology architecture draft for a knowledge-graph runtime.

Your job is NOT to extract every entity instance. Your job is to propose:
- a short snake_case domain
- entity types
- relation types
- normalization hints
- workflow hints
- tool affinity hints

Use the document evidence below. Favor concrete domain-specific type names.
Do not invent abstract junk labels like "thing", "object", "concept", or "entity".

Observed workspace priors (descriptive only, never mandatory):
- entity types: {known_entity_types}
- relation types: {known_relation_types}

Return STRICT JSON only:
{{
  "domain": "<snake_case_domain>",
  "entity_types": [
    {{
      "name": "<type_name>",
      "description": "<short description>",
      "attributes": [{{"name": "<snake_case>", "description": "<text>"}}],
      "normalization_hints": [{{"rule": "<rule_name>", "value": "<text>"}}],
      "evidence_refs": [{{"source_chunk_id": "<chunk_id>", "evidence_text": "<short quote>", "confidence": 0.0}}]
    }}
  ],
  "relation_types": [
    {{
      "name": "<type_name>",
      "description": "<short description>",
      "source_targets": [{{"source": "<entity_type>", "target": "<entity_type>"}}],
      "evidence_refs": [{{"source_chunk_id": "<chunk_id>", "evidence_text": "<short quote>", "confidence": 0.0}}]
    }}
  ],
  "normalization_hints": [{{"rule": "<rule_name>", "value": "<text>"}}],
  "workflow_hints": ["answer_resolution", "ontology_build"],
  "tool_affinity_hints": ["retrieval.internal", "ontology.lookup"],
  "summary": "<one short sentence>"
}}

Evidence:
{evidence}
"""


def build_architect_prompt(
    *,
    evidence: str,
    known_entity_types: Sequence[str],
    known_relation_types: Sequence[str],
) -> str:
    return _ARCHITECT_PROMPT.format(
        evidence=evidence,
        known_entity_types=_format_list(known_entity_types),
        known_relation_types=_format_list(known_relation_types),
    )


def _format_list(values: Sequence[str]) -> str:
    if not values:
        return "(none)"
    return ", ".join(values)
