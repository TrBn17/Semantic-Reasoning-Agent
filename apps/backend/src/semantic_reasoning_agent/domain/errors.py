from __future__ import annotations


class DomainError(Exception):
    """Base for all domain-level errors raised by the runtime."""


class ToolError(DomainError):
    """A tool failed during execution."""


class ExtractionError(DomainError):
    """Ontology or evidence extraction failed."""


class WorkflowError(DomainError):
    """A workflow step or transition failed."""
