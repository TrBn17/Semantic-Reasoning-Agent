import json
from types import SimpleNamespace

from semantic_reasoning_agent.domain.contracts.llm import LLMResponse
from semantic_reasoning_agent.domain.ontology.models import OntologyDocument
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.infrastructure.ontology.llm_extractor import OpenDomainLLMExtractor
from semantic_reasoning_agent.tools.ontology.schema_registry import EmergentSchema


class _FakeResolver:
    def is_ready(self, provider: str, model: str, workspace_id: str | None = None) -> bool:  # noqa: ANN001
        return provider == "openrouter" and model == "test-model" and workspace_id == "ws-1"


class _FakeSchemaRegistry:
    def for_workspace(self, workspace_id: str) -> EmergentSchema:
        return EmergentSchema(
            workspace_id=workspace_id,
            entity_types=("system",),
            relation_types=("depends_on",),
        )


class _QueueAdapter:
    provider = "openrouter"

    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = responses
        self.calls: list[dict[str, object]] = []

    def run(self, **kwargs) -> LLMResponse:  # noqa: ANN003
        self.calls.append(kwargs)
        return self._responses.pop(0)


def _build_extractor(responses: list[LLMResponse]) -> tuple[OpenDomainLLMExtractor, _QueueAdapter]:
    adapter = _QueueAdapter(responses)
    extractor = OpenDomainLLMExtractor(
        settings=SimpleNamespace(
            ontology_llm_enabled=True,
            ontology_markdown_char_limit=50000,
            ontology_prompt_version="v2",
            ontology_extraction_max_tokens=6000,
            ontology_extraction_reasoning_effort="low",
            ontology_extraction_max_chunks=8,
            ontology_extraction_entity_count_min=3,
            ontology_extraction_entity_count_max=50,
            ontology_classify_deferred_token="pending",
            default_workspace_id="workspace-demo",
        ),
        model_config_service=_FakeResolver(),
        schema_registry=_FakeSchemaRegistry(),
        adapter_registry=AdapterRegistry(adapters={"openrouter": adapter}),
    )
    return extractor, adapter


def test_extractor_sanitizes_think_blocks() -> None:
    extractor, _adapter = _build_extractor(
        [
            LLMResponse(
                content=(
                    "<think>internal</think>"
                    + json.dumps(
                        {
                            "domain": "ops",
                            "entities": [
                                {
                                    "name": "Alpha",
                                    "canonical_name": "Alpha",
                                    "resolution_key": "alpha",
                                    "entity_type": "system",
                                    "confidence": 0.8,
                                    "evidence_text": "Alpha integrates.",
                                    "aliases": [],
                                    "query_rules": [
                                        {
                                            "rule_id": "alpha-rule",
                                            "scope": "entity_type",
                                            "query_route": "hybrid",
                                            "trigger_keywords": ["integrates"],
                                        }
                                    ],
                                    "facts": [
                                        {
                                            "metric_key": "max_load",
                                            "value_num": 120.0,
                                            "unit": "kg",
                                        }
                                    ],
                                },
                                {
                                    "name": "Beta",
                                    "canonical_name": "Beta",
                                    "resolution_key": "beta",
                                    "entity_type": "system",
                                    "confidence": 0.8,
                                    "evidence_text": "Beta receives.",
                                    "aliases": [],
                                },
                            ],
                        }
                    )
                ),
                provider="openrouter",
                model="test-model",
            ),
            LLMResponse(
                content=json.dumps(
                    {
                        "relations": [
                            {
                                "source_resolution_key": "alpha",
                                "target_resolution_key": "beta",
                                "source_name": "Alpha",
                                "target_name": "Beta",
                                "relation_type": "depends_on",
                                "confidence": 0.77,
                                "evidence_text": "Alpha depends on Beta.",
                                "query_rules": [
                                    {
                                        "rule_id": "depends-rule",
                                        "scope": "relation_type",
                                        "query_route": "sql_facts",
                                        "trigger_keywords": ["depends"],
                                    }
                                ],
                                "facts": [{"metric_key": "dependency_count", "value_num": 1}],
                            }
                        ]
                    }
                ),
                provider="openrouter",
                model="test-model",
            ),
        ]
    )

    result = extractor.extract_ontology_candidates(
        OntologyDocument(document_id="doc-1", markdown="Alpha depends on Beta."),
        workspace_id="ws-1",
        provider="openrouter",
        model="test-model",
    )
    assert result.domain == "ops"
    assert len(result.entities) == 2
    assert len(result.relations) == 1
    assert result.entities[0].query_rules[0].query_route == "hybrid"
    assert result.entities[0].facts[0].metric_key == "max_load"
    assert result.relations[0].query_rules[0].query_route == "sql_facts"
    assert result.trace["errors"] == []


def test_extractor_retries_when_truncated_json() -> None:
    extractor, adapter = _build_extractor(
        [
            LLMResponse(
                content='{"domain":"ops","entities":[{"name":"Alpha"',
                finish_reason="max_tokens",
                provider="openrouter",
                model="test-model",
            ),
            LLMResponse(
                content=json.dumps(
                    {
                        "domain": "ops",
                        "entities": [
                            {
                                "name": "Alpha",
                                "canonical_name": "Alpha",
                                "resolution_key": "alpha",
                                "entity_type": "system",
                                "confidence": 0.8,
                                "evidence_text": "Alpha node.",
                                "aliases": [],
                            },
                            {
                                "name": "Beta",
                                "canonical_name": "Beta",
                                "resolution_key": "beta",
                                "entity_type": "system",
                                "confidence": 0.7,
                                "evidence_text": "Beta node.",
                                "aliases": [],
                            },
                        ],
                    }
                ),
                provider="openrouter",
                model="test-model",
            ),
            LLMResponse(
                content=json.dumps({"relations": []}),
                provider="openrouter",
                model="test-model",
            ),
        ]
    )
    result = extractor.extract_ontology_candidates(
        OntologyDocument(document_id="doc-1", markdown="Alpha and Beta."),
        workspace_id="ws-1",
        provider="openrouter",
        model="test-model",
    )
    assert len(result.entities) == 2
    assert result.trace["chunks"][0]["retried"] is True
    assert len(adapter.calls) == 3


def test_extractor_records_parse_error_when_empty_content() -> None:
    extractor, adapter = _build_extractor(
        [
            LLMResponse(
                content="",
                finish_reason="max_tokens",
                provider="openrouter",
                model="test-model",
            ),
            LLMResponse(
                content="",
                provider="openrouter",
                model="test-model",
            ),
        ]
    )
    result = extractor.extract_ontology_candidates(
        OntologyDocument(document_id="doc-1", markdown="Only one entity here."),
        workspace_id="ws-1",
        provider="openrouter",
        model="test-model",
    )
    assert result.entities == []
    assert result.relations == []
    assert len(result.trace["errors"]) >= 1
    assert "empty_payload" in result.trace["errors"][0]
    assert len(adapter.calls) == 2


def test_extractor_keeps_initial_payload_when_retry_is_empty() -> None:
    extractor, adapter = _build_extractor(
        [
            LLMResponse(
                content=json.dumps(
                    {
                        "domain": "ops",
                        "entities": [
                            {
                                "name": "Alpha",
                                "canonical_name": "Alpha",
                                "resolution_key": "alpha",
                                "entity_type": "system",
                                "confidence": 0.8,
                                "evidence_text": "Alpha node.",
                                "aliases": [],
                            },
                            {
                                "name": "Beta",
                                "canonical_name": "Beta",
                                "resolution_key": "beta",
                                "entity_type": "system",
                                "confidence": 0.7,
                                "evidence_text": "Beta node.",
                                "aliases": [],
                            },
                        ],
                    }
                ),
                finish_reason="max_tokens",
                provider="openrouter",
                model="test-model",
            ),
            LLMResponse(
                content="",
                provider="openrouter",
                model="test-model",
            ),
            LLMResponse(
                content=json.dumps({"relations": []}),
                provider="openrouter",
                model="test-model",
            ),
        ]
    )
    result = extractor.extract_ontology_candidates(
        OntologyDocument(document_id="doc-1", markdown="Alpha and Beta."),
        workspace_id="ws-1",
        provider="openrouter",
        model="test-model",
    )
    assert len(result.entities) == 2
    assert result.trace["chunks"][0]["retried"] is True
    assert "using_initial_payload" in str(result.trace["chunks"][0].get("parse_error"))
    assert len(adapter.calls) == 3


def test_extractor_merges_duplicate_entity_rows_without_dropping_rules_or_facts() -> None:
    extractor, adapter = _build_extractor(
        [
            LLMResponse(
                content=json.dumps(
                    {
                        "domain": "ops",
                        "entities": [
                            {
                                "name": "OpenRouter API Key",
                                "canonical_name": "OpenRouter API Key",
                                "resolution_key": "openrouter-api-key",
                                "entity_type": "api_key",
                                "confidence": 0.72,
                                "evidence_text": "Minimum monthly cost is $20.",
                                "aliases": ["OpenRouter Key"],
                                "query_rules": [
                                    {
                                        "rule_id": "cost-rule-a",
                                        "scope": "api_key",
                                        "query_route": "sql_facts",
                                    }
                                ],
                                "facts": [
                                    {
                                        "metric_key": "minimum_monthly_cost",
                                        "value_num": 20,
                                        "unit": "USD",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                provider="openrouter",
                model="test-model",
            ),
            LLMResponse(
                content=json.dumps(
                    {
                        "domain": "ops",
                        "entities": [
                            {
                                "name": "OpenRouter API Key",
                                "canonical_name": "OpenRouter API Key",
                                "resolution_key": "openrouter-api-key",
                                "entity_type": "api_key",
                                "confidence": 0.91,
                                "evidence_text": "Budget floor remains 20 USD monthly.",
                                "aliases": ["OpenRouter API Token"],
                                "query_rules": [
                                    {
                                        "rule_id": "cost-rule-b",
                                        "scope": "api_key",
                                        "query_route": "sql_facts",
                                    }
                                ],
                                "facts": [
                                    {
                                        "metric_key": "budget_floor",
                                        "value_num": 20,
                                        "unit": "USD",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                provider="openrouter",
                model="test-model",
            ),
        ]
    )

    extractor._FULL_PASS_MAX_INPUT_TOKENS = 0
    extractor._split_by_tokens = lambda text, max_tokens: ["chunk-a", "chunk-b"]  # type: ignore[method-assign]

    result = extractor.extract_ontology_candidates(
        OntologyDocument(document_id="doc-1", markdown="OpenRouter API Key appears multiple times."),
        workspace_id="ws-1",
        provider="openrouter",
        model="test-model",
    )

    assert len(result.entities) == 1
    merged = result.entities[0]
    assert merged.confidence == 0.91
    assert merged.evidence_text == "Budget floor remains 20 USD monthly."
    assert merged.aliases == {"OpenRouter Key", "OpenRouter API Token"}
    assert {rule.rule_id for rule in merged.query_rules} == {"cost-rule-a", "cost-rule-b"}
    assert {fact.metric_key for fact in merged.facts} == {"minimum_monthly_cost", "budget_floor"}
    assert len(result.relations) == 0
    assert len(adapter.calls) == 2
