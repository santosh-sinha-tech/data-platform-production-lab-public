"""Route validated immutable output; publication is atomic on a local filesystem."""

import shutil

from booking_pipeline.observability import emit, now, write_json
from booking_pipeline.quality import worst
from booking_pipeline.runtime import fingerprint, read_json, run_path


def route(root, run_id):
    report_path = run_path(root, "results", run_id) / "quality_result.json"
    report = read_json(report_path)
    status = report["data_quality_status"]
    checks_status = worst([report["volume_check_result"]["status"], report["null_check_result"]["status"],
                           report["reconciliation_result"]["status"]])
    decisions = {"PASS": "PUBLISH", "WARN": "PUBLISH_WITH_WARNING", "FAIL": "QUARANTINE"}
    if (report["run_id"] != run_id or status != checks_status or status not in decisions
            or report["publication_decision"] != decisions[status]
            or report["transformation_status"] != "SUCCESS"):
        raise ValueError("Inconsistent quality decision; publication blocked")
    source = run_path(root, "processed", run_id)
    if fingerprint(source) != report["processed_sha256"]:
        raise ValueError("Data changed after validation; publication blocked")
    area = "quarantine" if status == "FAIL" else "published"
    other_area = "published" if status == "FAIL" else "quarantine"
    if run_path(root, other_area, run_id).exists():
        raise FileExistsError("Conflicting existing disposition; publication blocked")
    target = run_path(root, area, run_id)
    marker = {"run_id": run_id, "data_quality_status": status,
              "publication_decision": report["publication_decision"], "processed_sha256": report["processed_sha256"]}
    if target.exists():
        # A retry after the rename can safely finish writing its result.
        if read_json(target / "_publication.json") != marker or fingerprint(target) != report["processed_sha256"]:
            raise ValueError("Existing destination does not match validated data")
    else:
        staging = run_path(root, "staging", run_id)
        # Stale staging is deliberately not trusted or overwritten; replay uses a new run id.
        shutil.copytree(source, staging)
        if fingerprint(staging) != report["processed_sha256"]:
            raise ValueError("Staged data does not match validation; publication blocked")
        # Spark ignores underscore-prefixed metadata alongside Parquet files.
        write_json(staging / "_publication.json", marker)
        target.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(target)
    report.update(publication_status="QUARANTINED" if status == "FAIL" else "PUBLISHED",
                  timestamp=now())
    write_json(report_path, report)
    emit("publication_completed", run_id=run_id, quality_gate_status=status,
         publication_status=report["publication_status"], level="WARNING" if status == "WARN" else "INFO")
    return report
