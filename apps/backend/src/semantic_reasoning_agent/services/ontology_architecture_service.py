from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select, update

from semantic_reasoning_agent.core.config import Settings
from semantic_reasoning_agent.domain.contracts.ontology_architecture import (
    OntologyArchitectureDraft,
    OntologyArchitectureEvidenceLink,
    OntologyArchitectureReview,
    OntologyArchitectureType,
)
from semantic_reasoning_agent.infrastructure.ontology.architecture_prompts import (
    build_architect_prompt,
)
from semantic_reasoning_agent.persistence.database import DatabaseManager
from semantic_reasoning_agent.persistence.models.ontology import (
    OntologyArchitectureDraftORM,
    OntologyArchitectureEvidenceLinkORM,
)
from semantic_reasoning_agent.persistence.repositories.ontology_repo import OntologyRepository
from semantic_reasoning_agent.ports.task_model_resolver import TaskModelResolverPort


@dataclass(frozen=True, slots=True)
class ArchitectureGrounding:
    draft: OntologyArchitectureDraft | None
    domain: str | None
    entity_hints: tuple[str, ...]
    relation_hints: tuple[str, ...]
    normalization_rules: tuple[dict, ...]
    workflow_hints: tuple[str, ...]
    tool_affinity_hints: tuple[str, ...]


class _EvidenceRef(BaseModel):
    source_chunk_id: str | None = None
    evidence_text: str = ""
    confidence: float = 0.0


class _DraftType(BaseModel):
    name: str
    description: str = ""
    attributes: list[dict] = Field(default_factory=list)
    source_targets: list[dict[str, str]] = Field(default_factory=list)
    normalization_hints: list[dict] = Field(default_factory=list)
    evidence_refs: list[_EvidenceRef] = Field(default_factory=list)


class _DraftPayload(BaseModel):
    domain: str = "general"
    entity_types: list[_DraftType] = Field(default_factory=list)
    relation_types: list[_DraftType] = Field(default_factory=list)
    normalization_hints: list[dict] = Field(default_factory=list)
    workflow_hints: list[str] = Field(default_factory=list)
    tool_affinity_hints: list[str] = Field(default_factory=list)
    summary: str = ""


class OntologyArchitectureService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_manager: DatabaseManager,
        ontology_repo: OntologyRepository,
        model_config_service: TaskModelResolverPort,
    ) -> None:
        self._settings = settings
        self._database_manager = database_manager
        self._ontology_repo = ontology_repo
        self._model_config_service = model_config_service

    def ensure_active_draft(
        self,
        *,
        workspace_id: str,
        source_document_ids: list[str],
        source_build_id: str | None = None,
        chunk_samples: list[tuple[str, str | None, str]] | None = None,
    ) -> OntologyArchitectureDraft:
        active = self.get_active_draft(workspace_id)
        if active is not None:
            return active
        return self.create_draft(
            workspace_id=workspace_id,
            source_document_ids=source_document_ids,
            source_build_id=source_build_id,
            chunk_samples=chunk_samples or [],
        )

    def get_active_draft(
        self,
        workspace_id: str,
        *,
        domain: str | None = None,
    ) -> OntologyArchitectureDraft | None:
        row = self._ontology_repo.get_active_architecture_draft(workspace_id, domain=domain)
        if row is None:
            return None
        with self._database_manager.session() as session:
            hydrated = session.scalar(
                select(OntologyArchitectureDraftORM).where(OntologyArchitectureDraftORM.id == row.id)
            )
            if hydrated is None:
                return None
            hydrated.evidence_links
            return self._to_contract(hydrated)

    def create_draft(
        self,
        *,
        workspace_id: str,
        source_document_ids: list[str],
        source_build_id: str | None,
        chunk_samples: list[tuple[str, str | None, str]],
    ) -> OntologyArchitectureDraft:
        payload, provenance = self._generate_payload(
            workspace_id=workspace_id,
            chunk_samples=chunk_samples,
        )
        review = self._review_payload(payload)

        draft_id = str(uuid4())
        now = datetime.utcnow().astimezone()
        entity_types = [self._sanitize_type(item, is_relation=False) for item in payload.entity_types]
        relation_types = [self._sanitize_type(item, is_relation=True) for item in payload.relation_types]
        workflow_hints = payload.workflow_hints or ["answer_resolution", "ontology_build"]
        tool_affinity_hints = payload.tool_affinity_hints or ["retrieval.internal", "ontology.lookup"]

        with self._database_manager.session() as session:
            session.execute(
                update(OntologyArchitectureDraftORM)
                .where(
                    OntologyArchitectureDraftORM.workspace_id == workspace_id,
                    OntologyArchitectureDraftORM.is_active.is_(True),
                )
                .values(is_active=False, updated_at=now)
            )
            row = OntologyArchitectureDraftORM(
                id=draft_id,
                workspace_id=workspace_id,
                source_document_ids=list(dict.fromkeys(source_document_ids)),
                source_build_id=source_build_id,
                domain=self._normalize_domain(payload.domain),
                status="approved",
                is_active=True,
                entity_types=[self._type_to_record(item) for item in entity_types],
                relation_types=[self._type_to_record(item) for item in relation_types],
                normalization_hints=list(payload.normalization_hints),
                workflow_hints=list(dict.fromkeys(workflow_hints)),
                tool_affinity_hints=list(dict.fromkeys(tool_affinity_hints)),
                review_summary=review.summary,
                review_findings=list(review.findings),
                provenance=provenance,
                created_at=now,
                updated_at=now,
            )
            session.add(row)

            evidence_links = self._collect_evidence_links(
                entity_types=entity_types,
                relation_types=relation_types,
                chunk_samples=chunk_samples,
            )
            for link in evidence_links:
                session.add(
                    OntologyArchitectureEvidenceLinkORM(
                        id=str(uuid4()),
                        draft_id=draft_id,
                        workspace_id=workspace_id,
                        source_document_id=link.source_document_id,
                        source_chunk_id=link.source_chunk_id,
                        link_kind=link.link_kind,
                        target_name=link.target_name,
                        evidence_text=link.evidence_text,
                        confidence=link.confidence,
                        created_at=now,
                    )
                )

        draft = self.get_active_draft(workspace_id, domain=self._normalize_domain(payload.domain))
        assert draft is not None
        return draft

    def build_grounding(self, workspace_id: str) -> ArchitectureGrounding:
        draft = self.get_active_draft(workspace_id)
        if draft is None:
            return ArchitectureGrounding(
                draft=None,
                domain=None,
                entity_hints=(),
                relation_hints=(),
                normalization_rules=(),
                workflow_hints=(),
                tool_affinity_hints=(),
            )
        return ArchitectureGrounding(
            draft=draft,
            domain=draft.domain,
            entity_hints=tuple(item.name for item in draft.entity_types),
            relation_hints=tuple(item.name for item in draft.relation_types),
            normalization_rules=draft.normalization_hints,
            workflow_hints=draft.workflow_hints,
            tool_affinity_hints=draft.tool_affinity_hints,
        )

    def _generate_payload(
        self,
        *,
        workspace_id: str,
        chunk_samples: list[tuple[str, str | None, str]],
    ) -> tuple[_DraftPayload, dict]:
        if not chunk_samples:
            payload = _DraftPayload(
                domain="general",
                workflow_hints=["answer_resolution", "ontology_build"],
                tool_affinity_hints=["retrieval.internal", "ontology.lookup"],
            )
            return payload, {"generator": "heuristic", "reason": "no_chunk_samples"}

        provider, model = self._model_config_service.resolve_task_model(
            "ontology_extraction",
            workspace_id,
        )
        if (
            not self._settings.ontology_llm_enabled
            or provider != "anthropic"
            or not self._model_config_service.is_ready(provider, model, workspace_id)
        ):
            return self._heuristic_payload(chunk_samples), {
                "generator": "heuristic",
                "provider": provider,
                "model": model,
            }

        prompt = build_architect_prompt(
            evidence=self._format_chunk_samples(chunk_samples),
            known_entity_types=self._ontology_repo.list_architecture_entity_types(workspace_id)
            or self._ontology_repo.list_used_entity_types(workspace_id),
            known_relation_types=self._ontology_repo.list_architecture_relation_types(workspace_id)
            or self._ontology_repo.list_used_relation_types(workspace_id),
        )
        payload_text = self._invoke_anthropic(prompt, workspace_id=workspace_id, model=model)
        try:
            parsed = _DraftPayload.model_validate(json.loads(payload_text))
        except (json.JSONDecodeError, ValidationError):
            parsed = self._heuristic_payload(chunk_samples)
            return parsed, {
                "generator": "heuristic_fallback",
                "provider": provider,
                "model": model,
                "prompt_version": self._settings.ontology_prompt_version,
            }
        return parsed, {
            "generator": "llm",
            "provider": provider,
            "model": model,
            "prompt_version": self._settings.ontology_prompt_version,
        }

    def _invoke_anthropic(self, prompt: str, *, workspace_id: str, model: str) -> str:
        from anthropic import Anthropic

        client_kwargs = {
            key: value
            for key, value in self._model_config_service.get_provider_runtime_config(
                "anthropic",
                workspace_id,
            ).items()
            if value
        }
        client = Anthropic(**client_kwargs)
        response = client.messages.create(
            model=model,
            max_tokens=2500,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        texts = [
            block.text
            for block in response.content
            if getattr(block, "type", "") == "text" and hasattr(block, "text")
        ]
        return "\n".join(texts).strip()

    def _review_payload(self, payload: _DraftPayload) -> OntologyArchitectureReview:
        findings: list[dict] = []
        blocked_names = {"thing", "concept", "object", "entity"}
        entity_names = [self._normalize_name(item.name) for item in payload.entity_types]
        relation_names = [self._normalize_name(item.name) for item in payload.relation_types]

        seen: set[str] = set()
        for name in entity_names:
            if not name:
                continue
            if name in blocked_names:
                findings.append({"severity": "medium", "type": "abstract_entity_type", "name": name})
            if name in seen:
                findings.append({"severity": "medium", "type": "duplicate_entity_type", "name": name})
            seen.add(name)

        seen.clear()
        for name in relation_names:
            if not name:
                continue
            if name in blocked_names:
                findings.append({"severity": "medium", "type": "abstract_relation_type", "name": name})
            if name in seen:
                findings.append({"severity": "medium", "type": "duplicate_relation_type", "name": name})
            seen.add(name)

        if not payload.entity_types:
            findings.append({"severity": "low", "type": "missing_entity_types"})
        if not payload.relation_types:
            findings.append({"severity": "low", "type": "missing_relation_types"})

        if findings:
            summary = f"Architecture draft reviewed with {len(findings)} finding(s)."
        else:
            summary = "Architecture draft reviewed with no blocking findings."
        return OntologyArchitectureReview(summary=summary, findings=tuple(findings))

    def _heuristic_payload(
        self,
        chunk_samples: list[tuple[str, str | None, str]],
    ) -> _DraftPayload:
        text = " ".join(text for _, _, text in chunk_samples)
        title_words = re.findall(r"\b[A-Z][a-zA-Z]{3,}\b", text)
        entity_names = []
        for value in title_words:
            normalized = self._normalize_name(value)
            if normalized and normalized not in entity_names:
                entity_names.append(normalized)
            if len(entity_names) >= 4:
                break
        entity_types = [
            _DraftType(
                name=name,
                description=f"Observed domain type related to {name}.",
                evidence_refs=[_EvidenceRef(source_chunk_id=chunk_samples[0][0], evidence_text=chunk_samples[0][2][:180], confidence=0.4)],
            )
            for name in entity_names
        ]
        relation_types = []
        if entity_types:
            relation_types.append(
                _DraftType(
                    name="related_to",
                    description="Generic relationship between document concepts.",
                    source_targets=[{"source": entity_types[0].name, "target": entity_types[-1].name}],
                    evidence_refs=[_EvidenceRef(source_chunk_id=chunk_samples[0][0], evidence_text=chunk_samples[0][2][:180], confidence=0.3)],
                )
            )
        return _DraftPayload(
            domain="general",
            entity_types=entity_types,
            relation_types=relation_types,
            normalization_hints=[{"rule": "trim_whitespace"}],
            workflow_hints=["answer_resolution", "ontology_build"],
            tool_affinity_hints=["retrieval.internal", "ontology.lookup"],
            summary="Heuristic architecture draft generated from representative chunks.",
        )

    @staticmethod
    def _format_chunk_samples(chunk_samples: list[tuple[str, str | None, str]]) -> str:
        parts: list[str] = []
        for chunk_id, document_id, text in chunk_samples:
            parts.append(
                f"[chunk_id={chunk_id}; document_id={document_id or ''}]\n{text[:1200]}"
            )
        return "\n\n".join(parts)

    @staticmethod
    def _normalize_domain(value: str | None) -> str:
        if not value:
            return "general"
        lowered = value.strip().lower()
        lowered = re.sub(r"[^a-z0-9_]+", "_", lowered)
        lowered = re.sub(r"_+", "_", lowered).strip("_")
        return lowered or "general"

    @staticmethod
    def _normalize_name(value: str | None) -> str:
        if not value:
            return ""
        lowered = value.strip().lower()
        lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
        lowered = re.sub(r"_+", "_", lowered).strip("_")
        return lowered

    def _sanitize_type(self, item: _DraftType, *, is_relation: bool) -> OntologyArchitectureType:
        name = self._normalize_name(item.name)
        if not name:
            name = "related_to" if is_relation else "document_subject"
        source_targets = tuple(
            {"source": self._normalize_name(edge.get("source")) or "document_subject", "target": self._normalize_name(edge.get("target")) or "document_subject"}
            for edge in item.source_targets
            if isinstance(edge, dict)
        )
        return OntologyArchitectureType(
            name=name,
            description=(item.description or f"Draft {'relation' if is_relation else 'entity'} type: {name}.").strip(),
            attributes=tuple(dict(attr) for attr in item.attributes if isinstance(attr, dict)),
            source_targets=source_targets,
            normalization_hints=tuple(
                dict(hint) for hint in item.normalization_hints if isinstance(hint, dict)
            ),
        )

    @staticmethod
    def _type_to_record(item: OntologyArchitectureType) -> dict:
        return {
            "name": item.name,
            "description": item.description,
            "attributes": [dict(attr) for attr in item.attributes],
            "source_targets": [dict(edge) for edge in item.source_targets],
            "normalization_hints": [dict(hint) for hint in item.normalization_hints],
        }

    def _collect_evidence_links(
        self,
        *,
        entity_types: list[OntologyArchitectureType],
        relation_types: list[OntologyArchitectureType],
        chunk_samples: list[tuple[str, str | None, str]],
    ) -> list[OntologyArchitectureEvidenceLink]:
        if not chunk_samples:
            return []
        default_chunk_id, default_document_id, default_text = chunk_samples[0]
        links: list[OntologyArchitectureEvidenceLink] = []
        for item in entity_types:
            links.append(
                OntologyArchitectureEvidenceLink(
                    link_kind="entity_type",
                    target_name=item.name,
                    source_chunk_id=default_chunk_id,
                    source_document_id=default_document_id,
                    evidence_text=default_text[:180],
                    confidence=0.35,
                )
            )
        for item in relation_types:
            links.append(
                OntologyArchitectureEvidenceLink(
                    link_kind="relation_type",
                    target_name=item.name,
                    source_chunk_id=default_chunk_id,
                    source_document_id=default_document_id,
                    evidence_text=default_text[:180],
                    confidence=0.3,
                )
            )
        return links

    def _to_contract(self, row: OntologyArchitectureDraftORM) -> OntologyArchitectureDraft:
        review = OntologyArchitectureReview(
            summary=row.review_summary or "",
            findings=tuple(row.review_findings or []),
        )
        entity_types = tuple(
            OntologyArchitectureType(
                name=str(item.get("name", "")),
                description=str(item.get("description", "")),
                attributes=tuple(item.get("attributes", []) or []),
                source_targets=tuple(item.get("source_targets", []) or []),
                normalization_hints=tuple(item.get("normalization_hints", []) or []),
            )
            for item in (row.entity_types or [])
            if isinstance(item, dict)
        )
        relation_types = tuple(
            OntologyArchitectureType(
                name=str(item.get("name", "")),
                description=str(item.get("description", "")),
                attributes=tuple(item.get("attributes", []) or []),
                source_targets=tuple(item.get("source_targets", []) or []),
                normalization_hints=tuple(item.get("normalization_hints", []) or []),
            )
            for item in (row.relation_types or [])
            if isinstance(item, dict)
        )
        evidence_links = tuple(
            OntologyArchitectureEvidenceLink(
                link_kind=link.link_kind,
                target_name=link.target_name,
                source_chunk_id=link.source_chunk_id,
                source_document_id=link.source_document_id,
                evidence_text=link.evidence_text,
                confidence=link.confidence,
            )
            for link in row.evidence_links
        )
        return OntologyArchitectureDraft(
            draft_id=row.id,
            workspace_id=row.workspace_id,
            source_document_ids=tuple(row.source_document_ids or []),
            domain=row.domain,
            status=row.status,
            entity_types=entity_types,
            relation_types=relation_types,
            normalization_hints=tuple(row.normalization_hints or []),
            workflow_hints=tuple(row.workflow_hints or []),
            tool_affinity_hints=tuple(row.tool_affinity_hints or []),
            review=review,
            evidence_links=evidence_links,
            provenance=dict(row.provenance or {}),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
