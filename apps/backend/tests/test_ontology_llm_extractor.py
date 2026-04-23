import json
from types import SimpleNamespace

from semantic_reasoning_agent.domain.contracts.llm import LLMResponse
from semantic_reasoning_agent.domain.ontology.models import OntologyDocument
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.infrastructure.ontology.llm_extractor import OpenDomainLLMExtractor
from semantic_reasoning_agent.tools.ontology.schema_registry import EmergentSchema


class _FakeModelResolver:
    def is_ready(  # noqa: ANN001
        self,
        provider: str,
        model: str,
        workspace_id: str | None = None,
    ) -> bool:
        return (
            provider == "openrouter"
            and model == "minimax/minimax-m2.5:free"
            and workspace_id == "workspace-openrouter"
        )


class _FakeSchemaRegistry:
    def for_workspace(self, workspace_id: str) -> EmergentSchema:
        assert workspace_id == "workspace-openrouter"
        return EmergentSchema(
            workspace_id=workspace_id,
            entity_types=("initiative",),
            relation_types=("depends_on",),
        )


class _FakeAdapter:
    provider = "openrouter"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run(self, **kwargs) -> LLMResponse:  # noqa: ANN003
        self.calls.append(kwargs)
        user_content = kwargs["messages"][0].content  # type: ignore[index]
        if "Extract candidate relations" in user_content:
            return LLMResponse(
                content=json.dumps(
                    {
                        "relations": [
                            {
                                "source_resolution_key": "gamma_program",
                                "target_resolution_key": "delta_system",
                                "source_name": "Gamma Program",
                                "target_name": "Delta System",
                                "relation_type": "depends_on",
                                "confidence": 0.91,
                                "evidence_text": "Gamma Program depends on Delta System.",
                            }
                        ]
                    }
                ),
                provider="openrouter",
                model="minimax/minimax-m2.5:free",
            )
        return LLMResponse(
            content=json.dumps(
                {
                    "domain": "delivery_ops",
                    "entities": [
                        {
                            "name": "Gamma Program",
                            "canonical_name": "Gamma Program",
                            "resolution_key": "gamma_program",
                            "entity_type": "initiative",
                            "confidence": 0.88,
                            "evidence_text": "Gamma Program depends on Delta System.",
                            "aliases": ["Program Gamma"],
                        },
                        {
                            "name": "Delta System",
                            "canonical_name": "Delta System",
                            "resolution_key": "delta_system",
                            "entity_type": "system",
                            "confidence": 0.93,
                            "evidence_text": "Gamma Program depends on Delta System.",
                            "aliases": [],
                        },
                    ],
                }
            ),
            provider="openrouter",
            model="minimax/minimax-m2.5:free",
        )


def test_open_domain_llm_extractor_supports_ready_non_anthropic_provider() -> None:
    fake_adapter = _FakeAdapter()
    extractor = OpenDomainLLMExtractor(
        settings=SimpleNamespace(
            ontology_llm_enabled=True,
            ontology_chunk_limit=24,
            ontology_markdown_char_limit=50000,
            ontology_prompt_version="v2",
            ontology_extraction_max_tokens=6000,
            ontology_extraction_reasoning_effort="low",
            ontology_extraction_max_chunks=8,
            default_workspace_id="workspace-demo",
        ),
        model_config_service=_FakeModelResolver(),
        adapter_registry=AdapterRegistry(adapters={"openrouter": fake_adapter}),
        schema_registry=_FakeSchemaRegistry(),
    )

    result = extractor.extract_ontology_candidates(
        OntologyDocument(
            document_id="doc-1",
            markdown="Gamma Program depends on Delta System.",
        ),
        workspace_id="workspace-openrouter",
        provider="openrouter",
        model="minimax/minimax-m2.5:free",
    )

    assert result.domain == "delivery_ops"
    assert [entity.resolution_key for entity in result.entities] == [
        "gamma_program",
        "delta_system",
    ]
    assert result.entities[0].aliases == {"Program Gamma"}
    assert result.entities[0].provenance["provider"] == "openrouter"
    assert result.entities[0].provenance["model"] == "minimax/minimax-m2.5:free"
    assert result.entities[0].provenance["source_document_id"] == "doc-1"
    assert [relation.relation_type for relation in result.relations] == ["depends_on"]

    assert isinstance(result.trace["chunks"], list)
    assert len(result.trace["chunks"]) == 2
    assert result.trace["errors"] == []
    assert result.trace["chunks"][0]["stage"] == "entities"
    assert result.trace["chunks"][1]["stage"] == "relations"

    assert len(fake_adapter.calls) == 2
    first_call = fake_adapter.calls[0]
    assert first_call["model"] == "minimax/minimax-m2.5:free"
    assert first_call["tool_choice"] == "none"
    assert first_call["tools"] == ()
    assert first_call["max_tokens"] == 6000
    assert first_call["temperature"] == 0
    assert first_call["response_format"] == "json_object"
    assert first_call["reasoning_effort"] == "low"
