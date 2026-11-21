"""Local policy fixtures. Only the trusted host selects principals and grants."""

import hashlib
import json
from pathlib import Path
from typing import Literal

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, PositiveInt, model_validator


class Fixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Principal(Fixture):
    subject: str
    tenant: str
    application: str = "fixture-client"
    role: str


PRINCIPALS = {
    "reader": Principal(subject="reader", tenant="alpha", role="reader"),
    "operator": Principal(subject="operator", tenant="alpha", role="operator"),
    "reviewer": Principal(subject="reviewer", tenant="alpha", role="approver"),
    "other_reviewer": Principal(subject="other_reviewer", tenant="beta", role="approver"),
}


class Credential(Fixture):
    audience: str
    tenant: str
    tool: str
    expires: float


class ServerRecord(Fixture):
    trust: Literal["approved", "pending"]
    version: PositiveInt
    owner: str
    environment: Literal["lab"]
    transport: Literal["stdio"]
    tools: list[str]


class Tool(Fixture):
    description: str
    risk: Literal["read", "write", "high"]
    roles: list[str]
    schema_: dict


class Policy(Fixture):
    protocol: Literal["2025-11-25"]
    servers: dict[str, ServerRecord]
    roles: dict[str, list[Literal["read", "write", "high"]]]
    tools: dict[str, Tool]
    targets: dict[str, str]

    @model_validator(mode="after")
    def validate_registry(self):
        for name, record in self.servers.items():
            if not record.owner or len(set(record.tools)) != len(record.tools):
                raise ValueError(f"invalid registry record: {name}")
            if set(record.tools) - self.tools.keys():
                raise ValueError(f"unknown registry tools: {name}")
        for tool in self.tools.values():
            if not tool.roles or set(tool.roles) - self.roles.keys():
                raise ValueError("invalid tool role grant")
            Draft202012Validator.check_schema(tool.schema_)
        return self


def load_policy(path: Path) -> Policy:
    data = json.loads(path.read_text())
    for tool in data["tools"].values():
        tool["schema_"] = tool.pop("schema")
    return Policy.model_validate(data)


def fingerprint(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def definition(name, description, schema):
    return fingerprint([name, description, schema])
