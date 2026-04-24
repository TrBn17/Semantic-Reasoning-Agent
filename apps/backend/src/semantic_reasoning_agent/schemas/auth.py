from pydantic import BaseModel


class WorkspaceSummary(BaseModel):
    id: str
    name: str


class WorkspaceCreateRequest(BaseModel):
    name: str


class WorkspaceUpdateRequest(BaseModel):
    name: str


class AuthMeResponse(BaseModel):
    id: str
    email: str
    display_name: str
    active_workspace: WorkspaceSummary
