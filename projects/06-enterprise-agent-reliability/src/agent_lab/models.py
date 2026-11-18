"""Strict contracts: external content never becomes executable instructions."""

from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Identity(Strict):
    tenant: Literal["alpha", "beta"]
    subject: str
    role: Literal["reader", "operator", "approver"]


class Args(Strict):
    resource: str = Field(default="synthetic-pipeline", pattern=r"^[a-z0-9-]{1,64}$")
    value: str = Field(default="safe", max_length=100)


class Action(Strict):
    tool: str
    args: Args = Field(default_factory=Args)
    fault: Literal[
        "none",
        "transient",
        "permanent",
        "timeout",
        "unknown",
        "interrupt",
        "invalid",
        "malicious",
    ] = "none"


class Request(Strict):
    key: str = Field(min_length=1, max_length=100)
    workflow: Literal["standard", "deploy", "rerun", "custom"] = "standard"
    actions: list[Action] | None = None


class Status(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    APPROVAL = "pending_approval"
    UNKNOWN = "unknown"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


EDGES = {
    "created": {"running", "failed", "cancelled"},
    "running": {"pending_approval", "unknown", "succeeded", "failed", "cancelled"},
    "pending_approval": {"running", "failed", "cancelled"},
    "unknown": {"running", "failed", "cancelled"},
    "succeeded": set(),
    "failed": set(),
    "cancelled": set(),
}


class Denied(Exception):
    pass


class Conflict(Exception):
    pass


class NotFound(Exception):
    pass


class Interrupted(Exception):
    pass


class Transient(Exception):
    pass


class Permanent(Exception):
    pass


class Unknown(Exception):
    pass
