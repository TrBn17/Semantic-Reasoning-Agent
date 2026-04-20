"""Ontology / knowledge-graph domain errors shared by services and HTTP layer."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OntologyBuildNotFoundError(ValueError):
    """Raised when an ontology build id does not exist."""


class OntologyBuildError(ValueError):
    """Raised when an ontology build cannot be created or processed."""


class OntologyPublishError(ValueError):
    """Raised when an ontology build cannot be published."""


class OntologyGraphError(ValueError):
    """Raised when the published graph cannot be read."""


class OntologyRelationNotFoundError(ValueError):
    """Raised when a published relation id does not exist."""
