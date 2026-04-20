from __future__ import annotations

from collections.abc import Sequence


_OPEN_DOMAIN_PROMPT = """You are extracting an ontology from the document below.

You may propose ANY entity_type and ANY relation_type that the text justifies.
Do NOT constrain yourself to a fixed list. Use specific, concrete type names
(e.g. "loan_product", "regulatory_clause", "team_role", "metric_definition")
rather than generic labels like "thing" / "concept" / "object".

Prior types observed in this workspace: use ONLY when they truly fit;
otherwise propose new ones. The list is descriptive, not prescriptive:
  entity types  : {known_entity_types}
  relation types: {known_relation_types}
  normalization : {normalization_hints}

Also classify the document into a short snake_case domain string.
Examples: "lending_policy", "process_handoff", "kpi_dashboard". You may
invent a new domain when none of the priors match.

Return STRICT JSON with this shape and NOTHING else:
{{
  "domain": "<snake_case_domain>",
  "entities": [
    {{
      "name": "<surface form>",
      "canonical_name": "<canonical>",
      "resolution_key": "<stable identifier>",
      "entity_type": "<your proposed type>",
      "confidence": 0.0,
      "evidence_text": "<short quote from document>",
      "aliases": []
    }}
  ],
  "relations": [
    {{
      "source_resolution_key": "<entity resolution_key>",
      "target_resolution_key": "<entity resolution_key>",
      "source_name": "<canonical>",
      "target_name": "<canonical>",
      "relation_type": "<your proposed type>",
      "confidence": 0.0,
      "evidence_text": "<short quote from document>"
    }}
  ]
}}

Prompt version: {prompt_version}

Document text:
{text}
"""


def build_open_domain_prompt(
    *,
    text: str,
    known_entity_types: Sequence[str],
    known_relation_types: Sequence[str],
    normalization_hints: Sequence[dict] | None,
    prompt_version: str,
) -> str:
    return _OPEN_DOMAIN_PROMPT.format(
        text=text,
        known_entity_types=_format_list(known_entity_types),
        known_relation_types=_format_list(known_relation_types),
        normalization_hints=_format_hints(normalization_hints or ()),
        prompt_version=prompt_version,
    )


def _format_list(values: Sequence[str]) -> str:
    if not values:
        return "(none observed yet - propose freely)"
    return ", ".join(values)


def _format_hints(values: Sequence[dict]) -> str:
    if not values:
        return "(none)"
    parts: list[str] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        rule = str(item.get("rule", "")).strip()
        value = str(item.get("value", "")).strip()
        if rule and value:
            parts.append(f"{rule}={value}")
        elif rule:
            parts.append(rule)
    return ", ".join(parts) if parts else "(none)"
