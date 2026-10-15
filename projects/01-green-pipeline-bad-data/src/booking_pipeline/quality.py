"""Quality rejection is a business result, not a processing exception."""

from decimal import Decimal

from pyspark.sql import functions as F

from booking_pipeline.contract import validate_contract
from booking_pipeline.observability import emit, now, write_json
from booking_pipeline.runtime import fingerprint, read_json, run_path

SEVERITY = {"PASS": 0, "WARN": 1, "FAIL": 2}


def worst(statuses):
    return max(statuses, key=SEVERITY.__getitem__)


def threshold_status(value, warning, failure):
    return "FAIL" if value > Decimal(str(failure)) else "WARN" if value > Decimal(str(warning)) else "PASS"


def evaluate(spark, root, run_id):
    manifest = read_json(run_path(root, "incoming", run_id) / "control.json")
    contract = validate_contract(manifest["contract"])
    expected = contract["expected_volume"]
    expected_amount = Decimal(manifest["expected_booking_amount"])
    if (manifest["run_id"] != run_id or manifest["records_expected"] != expected
            or manifest["currency"] != contract["currency"]
            or not expected_amount.is_finite() or expected_amount <= 0):
        raise ValueError("Invalid or inconsistent source controls")
    processed = run_path(root, "processed", run_id)
    data_digest = fingerprint(processed)
    frame = spark.read.parquet(str(processed))
    required = set(contract["mandatory_fields"]) | {contract["reconciliation"]["field"], "currency"}
    if not required <= set(frame.columns):
        raise ValueError(f"Missing contracted columns: {sorted(required - set(frame.columns))}")
    amount_field = contract["reconciliation"]["field"]
    expressions = [F.count(F.lit(1)).alias("received"), F.sum(amount_field).alias("amount"),
                   F.sum(F.when(F.col("currency").isNull() | (F.col("currency") != contract["currency"]), 1).otherwise(0)).alias("invalid_currency")]
    expressions += [F.sum(F.col(field).isNull().cast("long")).alias(f"null_{field}")
                    for field in contract["mandatory_fields"]]
    metrics = frame.agg(*expressions).first().asDict()
    if metrics["invalid_currency"]:
        raise ValueError("Mixed or missing currency makes this control total invalid")
    received = metrics["received"]
    completeness = Decimal(received) * 100 / expected
    volume_status = ("FAIL" if completeness < Decimal(str(contract["minimum_volume_percentage"]))
                     or completeness > Decimal(str(contract["maximum_volume_percentage"]))
                     else "WARN" if completeness < Decimal(str(contract["pass_volume_percentage"])) else "PASS")
    null_fields = {}
    for field in contract["mandatory_fields"]:
        count = metrics[f"null_{field}"] or 0
        percentage = Decimal(count) * 100 / received if received else Decimal(100)
        null_fields[field] = {
            "null_count": count, "null_percentage": float(percentage),
            "status": threshold_status(percentage, contract["warning_null_percentage"], contract["maximum_null_percentage"]),
        }
    actual_amount = metrics["amount"] or Decimal("0.00")
    variance = actual_amount - expected_amount
    variance_percentage = abs(variance) * 100 / expected_amount
    recon = contract["reconciliation"]
    reconciliation = {
        "status": threshold_status(variance_percentage, recon["warning_tolerance_percentage"], recon["tolerance_percentage"]),
        "expected_control_total": str(expected_amount), "processed_control_total": str(actual_amount),
        "variance": str(variance), "absolute_variance_percentage": float(variance_percentage),
        "tolerance_percentage": recon["tolerance_percentage"], "currency": contract["currency"],
    }
    null_status = worst([item["status"] for item in null_fields.values()])
    status = worst([volume_status, null_status, reconciliation["status"]])
    result = {
        "run_id": run_id, "scenario": manifest["scenario"], "contract_version": contract["contract_version"],
        "pipeline_status": "RUNNING", "orchestration_status": "RUNNING",
        "transformation_status": "SUCCESS", "data_quality_status": status,
        "records_expected": expected, "records_received": received,
        "completeness_percentage": float(completeness), "volume_check_result": {"status": volume_status},
        "null_check_result": {"status": null_status, "fields": null_fields},
        "reconciliation_result": reconciliation,
        "publication_decision": "QUARANTINE" if status == "FAIL" else "PUBLISH_WITH_WARNING" if status == "WARN" else "PUBLISH",
        "publication_status": "PENDING", "processed_sha256": data_digest, "timestamp": now(),
    }
    # Detect changes across the Spark read as well as before publication.
    if fingerprint(processed) != data_digest:
        raise RuntimeError("Processed data changed during validation")
    write_json(run_path(root, "results", run_id) / "quality_result.json", result)
    emit("quality_gate_evaluated", run_id=run_id, records_expected=expected, records_received=received,
         completeness_percentage=float(completeness),
         mandatory_field_null_percentage={field: value["null_percentage"] for field, value in null_fields.items()},
         reconciliation_variance=str(variance), quality_gate_status=status, publication_status="PENDING")
    return result
