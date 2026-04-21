from __future__ import annotations

from pydantic import BaseModel


class WorkflowSpecResponse(BaseModel):
    workflow_id: str
    name: str
    description: str
    deterministic: bool
