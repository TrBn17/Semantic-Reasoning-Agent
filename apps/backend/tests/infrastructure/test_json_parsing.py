from semantic_reasoning_agent.infrastructure.ontology.json_parsing import (
    parse_llm_json,
    sanitize_llm_json_payload,
)


def test_sanitize_llm_json_payload_strips_think_and_fences() -> None:
    raw = "<think>internal reasoning</think>\n```json\n{\"domain\":\"general\"}\n```"
    sanitized = sanitize_llm_json_payload(raw)
    assert sanitized == '{"domain":"general"}'


def test_parse_llm_json_handles_preamble_and_harmony_tags() -> None:
    raw = (
        "Here is the JSON:\n"
        "<|channel|>analysis<|end|>"
        "<|start|>assistant<|message|>"
        "{\"domain\":\"ops\",\"entities\":[]}"
    )
    payload, error = parse_llm_json(raw)
    assert error is None
    assert payload == {"domain": "ops", "entities": []}


def test_parse_llm_json_returns_error_for_invalid_json() -> None:
    payload, error = parse_llm_json("{\"domain\":")
    assert payload is None
    assert isinstance(error, str)
    assert "json_decode_error" in error


def test_parse_llm_json_recovers_partial_entities_array() -> None:
    raw = (
        '{"domain":"ops","entities":['
        '{"name":"A","canonical_name":"A","resolution_key":"a","entity_type":"system","confidence":0.9,"evidence_text":"A"},'
        '{"name":"B","canonical_name":"B","resolution_key":"b","entity_type":"system","confidence":0.7,"evidence_text":"B"}'
    )
    payload, error = parse_llm_json(raw)
    assert isinstance(payload, dict)
    assert payload["domain"] == "ops"
    assert len(payload["entities"]) == 2
    assert isinstance(error, str)
    assert "json_recovered_partial" in error
