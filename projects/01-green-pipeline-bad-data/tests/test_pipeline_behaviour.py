import shutil
from decimal import Decimal

import pytest
import yaml
from pyspark.sql import functions as F

from booking_pipeline.generator import generate
from booking_pipeline.observability import write_json
from booking_pipeline.publication import route
from booking_pipeline.quality import evaluate
from booking_pipeline.runtime import fingerprint, read_json, run_path
from booking_pipeline.transformation import transform


def prepare(spark, root, contract, scenario="healthy"):
    generate(spark, root, "test-run", scenario, contract)
    transform(spark, root, "test-run")


def replace_processed(spark, root, change):
    path = run_path(root, "processed", "test-run")
    temporary = root / "replacement"
    change(spark.read.parquet(str(path))).write.parquet(str(temporary))
    shutil.rmtree(path)
    temporary.rename(path)


@pytest.mark.parametrize("scenario,count,status,area", [
    ("healthy", 1000, "PASS", "published"),
    ("incomplete-source", 820, "FAIL", "quarantine"),
])
def test_pipeline_routes_actual_parquet(spark, tmp_path, contract_path, scenario, count, status, area):
    prepare(spark, tmp_path, contract_path, scenario)
    result = evaluate(spark, tmp_path, "test-run")
    routed = route(tmp_path, "test-run")
    assert result["data_quality_status"] == status
    assert result["records_received"] == count
    assert result["completeness_percentage"] == count / 10
    assert result["transformation_status"] == "SUCCESS"
    assert result["orchestration_status"] == "RUNNING"  # These tests do not run Airflow.
    assert spark.read.parquet(str(run_path(tmp_path, area, "test-run"))).count() == count
    assert routed["publication_status"] == ("PUBLISHED" if status == "PASS" else "QUARANTINED")
    if status == "FAIL":
        assert not run_path(tmp_path, "published", "test-run").exists()
        assert result["reconciliation_result"]["status"] == "FAIL"


def test_mandatory_nulls_quarantine_even_with_matching_volume_and_amount(spark, tmp_path, contract_path):
    prepare(spark, tmp_path, contract_path)
    replace_processed(spark, tmp_path, lambda df: df.withColumn("customer_id", F.lit(None).cast("string")))
    result = evaluate(spark, tmp_path, "test-run")
    assert result["volume_check_result"]["status"] == "PASS"
    assert result["reconciliation_result"]["status"] == "PASS"
    assert result["null_check_result"]["fields"]["customer_id"]["null_percentage"] == 100
    assert route(tmp_path, "test-run")["publication_status"] == "QUARANTINED"
    assert not run_path(tmp_path, "published", "test-run").exists()


@pytest.mark.parametrize("factor,expected_status,publication", [
    ("1.10", "FAIL", "QUARANTINED"), ("1.001", "WARN", "PUBLISHED"),
])
def test_amount_mismatch_routes_by_configured_tolerance(spark, tmp_path, contract_path, factor, expected_status, publication, capsys):
    prepare(spark, tmp_path, contract_path)
    replace_processed(spark, tmp_path, lambda df: df.withColumn(
        "booking_amount", (F.col("booking_amount") * F.lit(Decimal(factor))).cast("decimal(18,2)")))
    result = evaluate(spark, tmp_path, "test-run")
    assert result["volume_check_result"]["status"] == "PASS"
    assert result["null_check_result"]["status"] == "PASS"
    assert result["reconciliation_result"]["status"] == expected_status
    assert route(tmp_path, "test-run")["publication_status"] == publication
    if expected_status == "WARN":
        assert '"level": "WARNING"' in capsys.readouterr().out
    else:
        assert not run_path(tmp_path, "published", "test-run").exists()


def test_publication_blocks_data_changed_after_validation(spark, tmp_path, contract_path):
    prepare(spark, tmp_path, contract_path)
    evaluate(spark, tmp_path, "test-run")
    replace_processed(spark, tmp_path, lambda df: df.limit(820))
    with pytest.raises(ValueError, match="changed after validation"):
        route(tmp_path, "test-run")
    assert not run_path(tmp_path, "published", "test-run").exists()


def test_fail_cannot_be_overridden_by_publish_decision(spark, tmp_path, contract_path):
    prepare(spark, tmp_path, contract_path, "incomplete-source")
    result = evaluate(spark, tmp_path, "test-run")
    result["publication_decision"] = "PUBLISH"
    write_json(run_path(tmp_path, "results", "test-run") / "quality_result.json", result)
    with pytest.raises(ValueError, match="Inconsistent"):
        route(tmp_path, "test-run")
    assert not run_path(tmp_path, "published", "test-run").exists()


def test_publication_retry_is_idempotent_and_run_reuse_is_blocked(spark, tmp_path, contract_path):
    prepare(spark, tmp_path, contract_path)
    evaluate(spark, tmp_path, "test-run")
    route(tmp_path, "test-run")
    before = fingerprint(run_path(tmp_path, "published", "test-run"))
    assert route(tmp_path, "test-run")["publication_status"] == "PUBLISHED"
    assert fingerprint(run_path(tmp_path, "published", "test-run")) == before
    with pytest.raises(FileExistsError, match="Run already exists"):
        generate(spark, tmp_path, "test-run", "incomplete-source", contract_path)
    assert fingerprint(run_path(tmp_path, "published", "test-run")) == before


def test_storage_failure_leaves_trusted_directory_empty(spark, tmp_path, contract_path, monkeypatch):
    prepare(spark, tmp_path, contract_path)
    evaluate(spark, tmp_path, "test-run")

    def broken_copy(source, target):
        target.mkdir(parents=True)
        (target / "partial.parquet").write_bytes(b"incomplete copy")
        raise OSError("simulated storage failure")

    monkeypatch.setattr("booking_pipeline.publication.shutil.copytree", broken_copy)
    with pytest.raises(OSError, match="storage failure"):
        route(tmp_path, "test-run")
    assert not run_path(tmp_path, "published", "test-run").exists()
    assert read_json(run_path(tmp_path, "results", "test-run") / "quality_result.json")["publication_status"] == "PENDING"


@pytest.mark.parametrize("keep,expected_status", [(950, "WARN"), (949, "FAIL"), (0, "FAIL")])
def test_volume_boundary_and_empty_delivery(spark, tmp_path, contract_path, keep, expected_status):
    config = yaml.safe_load(contract_path.read_text())
    # Isolate completeness while retaining real reconciliation metrics.
    config["reconciliation"]["tolerance_percentage"] = 100
    config["reconciliation"]["warning_tolerance_percentage"] = 100
    contract_path.write_text(yaml.safe_dump(config))
    prepare(spark, tmp_path, contract_path)
    replace_processed(spark, tmp_path, lambda df: df.limit(keep))
    result = evaluate(spark, tmp_path, "test-run")
    assert result["volume_check_result"]["status"] == expected_status
    assert route(tmp_path, "test-run")["data_quality_status"] == expected_status


def test_missing_controls_fail_closed(spark, tmp_path, contract_path):
    prepare(spark, tmp_path, contract_path)
    (run_path(tmp_path, "incoming", "test-run") / "control.json").unlink()
    with pytest.raises(FileNotFoundError):
        evaluate(spark, tmp_path, "test-run")
    with pytest.raises(FileNotFoundError):
        route(tmp_path, "test-run")
    assert not run_path(tmp_path, "published", "test-run").exists()


@pytest.mark.parametrize("invalid_input", ["missing-column", "mixed-currency"])
def test_unusable_data_cannot_get_a_publishable_decision(spark, tmp_path, contract_path, invalid_input):
    prepare(spark, tmp_path, contract_path)
    if invalid_input == "missing-column":
        replace_processed(spark, tmp_path, lambda df: df.drop("customer_id"))
    else:
        replace_processed(spark, tmp_path, lambda df: df.withColumn("currency", F.lit("EUR")))
    with pytest.raises(ValueError):
        evaluate(spark, tmp_path, "test-run")
    with pytest.raises(FileNotFoundError):
        route(tmp_path, "test-run")
    assert not run_path(tmp_path, "published", "test-run").exists()
