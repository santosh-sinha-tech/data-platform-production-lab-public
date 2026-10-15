"""Verify final Airflow evidence AND persisted Parquet, not just console messages."""

import argparse
from pathlib import Path

from booking_pipeline.runtime import fingerprint, read_json, run_path, spark_session


def verify(root, healthy_id, incomplete_id):
    spark = spark_session()
    try:
        for run_id, count, status, area in [(healthy_id, 100000, "PASS", "published"),
                                           (incomplete_id, 82000, "FAIL", "quarantine")]:
            report = read_json(run_path(root, "results", run_id) / "quality_result.json")
            assert report["pipeline_status"] == report["orchestration_status"] == "SUCCESS"
            assert report["transformation_status"] == "SUCCESS"
            assert report["airflow_task_states"] == {
                "synthetic_source": "success", "pyspark_transformation": "success",
                "data_quality_gate": "success", "publication_router": "success",
            }
            assert report["records_expected"] == 100000
            assert report["records_received"] == count
            assert report["completeness_percentage"] == count / 1000
            assert report["data_quality_status"] == status
            assert report["publication_status"] == ("PUBLISHED" if status == "PASS" else "QUARANTINED")
            target = run_path(root, area, run_id)
            assert spark.read.parquet(str(target)).count() == count
            assert fingerprint(target) == report["processed_sha256"]
            other_area = "published" if area == "quarantine" else "quarantine"
            assert not run_path(root, other_area, run_id).exists()
            print(f"VERIFIED {run_id}: {count:,} rows, {status}, {area}; all four Airflow tasks succeeded")
        print("VERIFIED: incomplete-source run has no trusted published partition")
    finally:
        spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--healthy-run", default="healthy-demo")
    parser.add_argument("--incomplete-run", default="incomplete-demo")
    args = parser.parse_args()
    verify(args.data_root, args.healthy_run, args.incomplete_run)
