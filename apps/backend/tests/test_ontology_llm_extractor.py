import json
from types import SimpleNamespace

from semantic_reasoning_agent.domain.contracts.llm import LLMResponse
from semantic_reasoning_agent.domain.ontology.models import OntologySourceChunk
from semantic_reasoning_agent.infrastructure.llm.registry import AdapterRegistry
from semantic_reasoning_agent.infrastructure.ontology.llm_extractor import OpenDomainLLMExtractor
from semantic_reasoning_agent.tools.ontology.schema_registry import EmergentSchema


class _FakeModelResolver:
    def resolve_task_model(  # noqa: ANN001
        self,
        task_type: str,
        workspace_id: str | None = None,
        agent_profile_id: str | None = None,
    ) -> tuple[str, str]:
        assert task_type == "ontology_extraction"
        assert workspace_id == "workspace-openrouter"
        return "openrouter", "minimax/minimax-m2.5:free"

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
        return LLMResponse(
            content=json.dumps(
                {
                    "domain": "delivery_ops",
                    "entities": [
                        {
                            "name": "Gamma Program",
                            "canonical_name": "Gamma Program",
                            "resolution_key": "gamma-program",
                            "entity_type": "initiative",
                            "confidence": 0.88,
                            "evidence_text": "Gamma Program depends on Delta System.",
                            "aliases": ["Program Gamma"],
                        },
                        {
                            "name": "Delta System",
                            "canonical_name": "Delta System",
                            "resolution_key": "delta-system",
                            "entity_type": "system",
                            "confidence": 0.93,
                            "evidence_text": "Gamma Program depends on Delta System.",
                            "aliases": [],
                        },
                    ],
                    "relations": [
                        {
                            "source_resolution_key": "gamma-program",
                            "target_resolution_key": "delta-system",
                            "source_name": "Gamma Program",
                            "target_name": "Delta System",
                            "relation_type": "depends_on",
                            "confidence": 0.91,
                            "evidence_text": "Gamma Program depends on Delta System.",
                        }
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
            ontology_prompt_version="v1",
            default_workspace_id="workspace-demo",
        ),
        model_config_service=_FakeModelResolver(),
        adapter_registry=AdapterRegistry(adapters={"openrouter": fake_adapter}),
        schema_registry=_FakeSchemaRegistry(),
    )

    result = extractor.extract_ontology_candidates(
        [
            OntologySourceChunk(
                chunk_id="chunk-1",
                text="Gamma Program depends on Delta System.",
            )
        ],
        workspace_id="workspace-openrouter",
    )

    assert result.domain == "delivery_ops"
    assert [entity.resolution_key for entity in result.entities] == [
        "gamma-program",
        "delta-system",
    ]
    assert result.entities[0].aliases == {"Program Gamma"}
    assert result.entities[0].provenance["provider"] == "openrouter"
    assert result.entities[0].provenance["model"] == "minimax/minimax-m2.5:free"
    assert result.entities[0].provenance["source_chunk_id"] == "chunk-1"
    assert [relation.relation_type for relation in result.relations] == ["depends_on"]

    assert len(fake_adapter.calls) == 1
    call = fake_adapter.calls[0]
    assert call["model"] == "minimax/minimax-m2.5:free"
    assert call["tool_choice"] == "none"
    assert call["tools"] == ()
    assert call["max_tokens"] == 3000
    assert call["temperature"] == 0
