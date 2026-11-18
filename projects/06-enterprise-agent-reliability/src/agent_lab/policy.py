import hashlib
import json
from typing import Any
from .models import Action, Denied, Identity, Request
from .tools import TOOLS

PERMISSIONS = {
    "reader": {"read"},
    "operator": {"read", "write", "deploy", "rerun"},
    "approver": {"read"},
}


def digest(action: Action) -> str:
    return hashlib.sha256(
        json.dumps(action.model_dump(), sort_keys=True).encode()
    ).hexdigest()


def plan(request: Request) -> list[Action]:
    if request.workflow == "custom":
        if request.actions is None:
            raise Denied("custom workflow needs actions")
        return request.actions
    if request.actions is not None:
        raise Denied("actions only allowed with custom")
    names = {
        "standard": ["read_quality", "get_runbook", "create_ticket", "notify_ops"],
        "deploy": ["read_quality", "update_deployment"],
        "rerun": ["read_quality", "rerun_pipeline"],
    }[request.workflow]
    return [Action(tool=name) for name in names]


def authorize(
    identity: Identity,
    owner_tenant: str,
    action: Action,
    all_actions: list[Action],
    config: dict[str, Any],
) -> None:
    if identity.tenant != owner_tenant:
        raise Denied("tenant isolation")
    tool = TOOLS.get(action.tool)
    if tool is None or tool.permission not in PERMISSIONS[identity.role]:
        raise Denied("tool permission")
    tool.input_schema.model_validate(action.args.model_dump())
    if len(all_actions) > config["max_steps"]:
        raise Denied("workflow depth")
    names = {a.tool for a in all_actions}
    if {"update_deployment", "rerun_pipeline"} <= names:
        raise Denied("prohibited action combination")
