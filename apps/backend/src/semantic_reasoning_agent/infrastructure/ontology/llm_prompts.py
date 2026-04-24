from __future__ import annotations

from collections.abc import Sequence

_ENTITY_SYSTEM_PROMPT = """You are an ontology extraction service.
You MUST return ONLY valid JSON object output and no extra text.
Do NOT include analysis, reasoning, markdown fences, or explanations.
Use snake_case for domain and type names when possible."""

_ENTITY_USER_PROMPT = """Extract candidate entities from the document.

Rules:
- You may propose ANY entity_type justified by the text.
- Prior entity types are descriptive hints only: {known_entity_types}
- Return {entity_count_min}-{entity_count_max} entities when the text supports that range; return fewer when the text is sparse.
- Every entity must include direct evidence_text copied from the document.
- confidence is in [0, 1].
- resolution_key must be stable snake_case.
- If the text implies when/how a query should be routed, include query_rules using the shared shape below.
- If the text contains measurable values (threshold, setpoint, numeric metric, status flag), include facts.

Shared query_rules shape (list):
[
  {{
    "rule_id": "<stable-id>",
    "scope": "entity_type",
    "query_route": "graph|sql_facts|hybrid",
    "trigger_keywords": [],
    "intent_tags": [],
    "required_fields": [],
    "aggregation": "latest|avg|min|max|window",
    "confidence_threshold": 0.0,
    "fallback_route": "graph|sql_facts|hybrid",
    "metadata": {{}}
  }}
]

facts shape (list):
[
  {{
    "metric_key": "<snake_case_metric>",
    "value_num": 0.0,
    "value_text": null,
    "value_bool": null,
    "unit": "<optional-unit>",
    "observed_at": "<iso8601 or null>",
    "source_chunk_id": null,
    "metadata": {{}}
  }}
]

Return STRICT JSON exactly in this shape:
{{
  "domain": "<snake_case_domain>",
  "entities": [
    {{
      "name": "<surface form>",
      "canonical_name": "<canonical>",
      "resolution_key": "<stable identifier>",
      "entity_type": "<proposed type>",
      "confidence": 0.0,
      "evidence_text": "<short quote from document>",
      "aliases": [],
      "query_rules": [],
      "facts": []
    }}
  ]
}}

Prompt version: {prompt_version}

Document text:
{text}
"""

_RELATION_SYSTEM_PROMPT = """You are an ontology extraction service.
You MUST return ONLY valid JSON object output and no extra text.
Do NOT include analysis, reasoning, markdown fences, or explanations."""

_RELATION_USER_PROMPT = """Extract candidate relations from the document.

Rules:
- Prior relation types are descriptive hints only: {known_relation_types}
- Existing entities observed so far (hints only, not a hard constraint):
{entity_whitelist}
- You may propose additional entities as relation endpoints when strongly grounded in the text; keep resolution_key stable snake_case.
- You may infer relations that are clearly implied by the document: structure (headings, phases, tables), roles and staffing, timelines, cost rows, and narrative flow, even when a single quote does not name both endpoints. When inferring, use confidence below 1.0 if needed, and in evidence_text briefly state the table/section and the inference (e.g. "Staffing plan rows 1-3: role X and milestone Y in the same project plan").
- Do not invent relations with no defensible link to the document; prefer fewer, grounded edges.
- confidence is in [0, 1].
- Include query_rules when a relation encodes operational policy/trigger semantics.
- Include facts for non-graphable measurements/events tied to this relation.

Return STRICT JSON exactly in this shape:
{{
  "relations": [
    {{
      "source_resolution_key": "<entity resolution_key>",
      "target_resolution_key": "<entity resolution_key>",
      "source_name": "<canonical>",
      "target_name": "<canonical>",
      "relation_type": "<proposed type>",
      "confidence": 0.0,
      "evidence_text": "<short quote or 1-2 line justification: quote(s) and/or structural basis per rules above>",
      "query_rules": [],
      "facts": []
    }}
  ]
}}

Prompt version: {prompt_version}

Document text:
{text}
"""

_SUMMARY_SYSTEM_PROMPT = """You generate concise ontology metadata.
Return strict JSON with keys title and summary only."""

_SUMMARY_USER_PROMPT = """Generate concise ontology metadata from the document text.
Rules:
- title: 3 to 8 words, descriptive, no quotes.
- summary: 1 sentence, <= 180 chars.
- domain hint: {domain}

Return STRICT JSON:
{{
  "title": "<title>",
  "summary": "<summary>"
}}

Document text:
{text}
"""


def build_entity_extraction_prompt(
    *,
    text: str,
    known_entity_types: Sequence[str],
    prompt_version: str,
    entity_count_min: int,
    entity_count_max: int,
) -> tuple[str, str]:
    return (
        _ENTITY_SYSTEM_PROMPT,
        _ENTITY_USER_PROMPT.format(
            text=text,
            known_entity_types=_format_list(known_entity_types),
            prompt_version=prompt_version,
            entity_count_min=entity_count_min,
            entity_count_max=entity_count_max,
        ),
    )


def build_relation_extraction_prompt(
    *,
    text: str,
    entity_whitelist: Sequence[str],
    known_relation_types: Sequence[str],
    prompt_version: str,
) -> tuple[str, str]:
    return (
        _RELATION_SYSTEM_PROMPT,
        _RELATION_USER_PROMPT.format(
            text=text,
            entity_whitelist=_format_whitelist(entity_whitelist),
            known_relation_types=_format_list(known_relation_types),
            prompt_version=prompt_version,
        ),
    )


def build_summary_prompt(
    *,
    text: str,
    domain: str,
) -> tuple[str, str]:
    return (
        _SUMMARY_SYSTEM_PROMPT,
        _SUMMARY_USER_PROMPT.format(
            text=text,
            domain=domain,
        ),
    )


def build_open_domain_prompt(
    *,
    text: str,
    known_entity_types: Sequence[str],
    known_relation_types: Sequence[str],
    prompt_version: str,
    entity_count_min: int = 3,
    entity_count_max: int = 50,
) -> str:
    """Backward compatibility helper for legacy tests."""
    system, user = build_entity_extraction_prompt(
        text=text,
        known_entity_types=known_entity_types,
        prompt_version=prompt_version,
        entity_count_min=entity_count_min,
        entity_count_max=entity_count_max,
    )
    return (
        f"{system}\n\n"
        f"Relation type hints: {_format_list(known_relation_types)}\n\n"
        f"{user}"
    )


def _format_list(values: Sequence[str]) -> str:
    if not values:
        return "(none observed yet — propose freely)"
    return ", ".join(values)


def _format_whitelist(values: Sequence[str]) -> str:
    if not values:
        return "(empty)"
    return "\n".join(f"- {value}" for value in values)
