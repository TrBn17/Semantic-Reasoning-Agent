from __future__ import annotations

DOMAIN_PROMPT_TEMPLATES: dict[str, str] = {
    "policy": "Extract policy entities, controls, approvals, owners, and compliance relationships.",
    "process": "Extract process steps, systems, teams, dependencies, and handoff relationships.",
    "org": "Extract organizational units, roles, responsibilities, and ownership relationships.",
    "metrics": "Extract metrics, dimensions, report artifacts, and tracking relationships.",
    "spreadsheet": "Extract KPI/metric entities, dimensions, dataset concepts, and applies_to relations.",
    "general": "Extract concepts, entities, systems, and explicit semantic relations with evidence.",
}


def build_extraction_prompt(*, domain: str, text: str, prompt_version: str) -> str:
    domain_instruction = DOMAIN_PROMPT_TEMPLATES.get(domain, DOMAIN_PROMPT_TEMPLATES["general"])
    return (
        f"Prompt version: {prompt_version}\n"
        "Return strict JSON with keys: entities, relations.\n"
        "Entity fields: name, canonical_name, resolution_key, entity_type, confidence, evidence_text, aliases.\n"
        "Relation fields: source_resolution_key, target_resolution_key, source_name, target_name, relation_type, confidence, evidence_text.\n"
        "Only return JSON.\n"
        f"Domain instruction: {domain_instruction}\n\n"
        f"Document text:\n{text}"
    )
