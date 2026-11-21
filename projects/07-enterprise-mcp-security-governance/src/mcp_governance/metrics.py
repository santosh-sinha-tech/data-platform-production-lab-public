"""Deterministic summaries from independent scenario and timing samples."""

import math
from collections import Counter
from statistics import mean


def latency(values):
    values = sorted(value for value in values if value is not None)
    if not values:
        return {"n": 0}
    summary = {"n": len(values), "mean": mean(values), "min": values[0], "max": values[-1]}
    for quantile in (50, 95, 99):
        summary[f"p{quantile}"] = values[math.ceil(len(values) * quantile / 100) - 1]
    return summary


def summarize(cases):
    outcomes = Counter(row["outcome"] for row in cases)
    policy_denials = {"unapproved_server", "unauthorized_tool", "tenant_mismatch",
                      "definition_drift", "credential_audience", "approval_expired",
                      "approval_replay", "duplicate"}
    prevention = [row for row in cases if row["case"] in "BCDEFGHIJL"]
    drift = [row for row in cases if row["case"] in "EF"]
    return {
        "scenario_trials": len(cases),
        "scenario_passes": sum(row["passed"] for row in cases),
        "policy_denials": sum(outcomes[name] for name in policy_denials),
        "policy_denial_rate": sum(outcomes[name] for name in policy_denials) / len(cases),
        "drift_detected": sum(row["outcome"] == "definition_drift" for row in drift),
        "drift_trials": len(drift),
        "prevention_passes": sum(row["passed"] for row in prevention),
        "prevention_trials": len(prevention),
        "complete_audits": sum(row["audit_complete"] for row in cases),
        "recovery": dict(Counter(row["recovery"] for row in cases
                                 if row["recovery"] != "not_applicable")),
        "outcomes": dict(sorted(outcomes.items())),
        "approval_wait_ms": latency(row["approval_wait_ms"] for row in cases),
    }


def prometheus(metrics):
    lines = ["# TYPE mcp_lab_scenario_trials gauge",
             f'mcp_lab_scenario_trials {metrics["scenario_trials"]}',
             "# TYPE mcp_lab_policy_denial_ratio gauge",
             f'mcp_lab_policy_denial_ratio {metrics["policy_denial_rate"]}',
             "# TYPE mcp_lab_outcomes gauge"]
    lines.extend(f'mcp_lab_outcomes{{outcome="{name}"}} {count}'
                 for name, count in metrics["outcomes"].items())
    return "\n".join(lines) + "\n"
