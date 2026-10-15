"""Run the real Airflow DAG synchronously and report its observed final state."""

import argparse
import subprocess
from pathlib import Path
from uuid import uuid4

from booking_pipeline.observability import emit, now, write_json
from booking_pipeline.runtime import read_json, run_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def execute(scenario, data_root, contract_path, run_id):
    root = Path(data_root).resolve()
    for area in ("incoming", "processed", "published", "quarantine", "results", "staging"):
        if run_path(root, area, run_id).exists():
            raise FileExistsError(f"Run already exists: {run_id}; use a new run_id")
    # The metadata database lives only inside this one-shot local container.
    subprocess.run(["airflow", "db", "migrate"], check=True)
    from booking_readiness import dag

    try:
        run = dag.test(run_conf={"scenario": scenario, "run_id": run_id,
                                 "data_root": str(root), "contract_path": str(Path(contract_path).resolve())})
        task_states = {task.task_id: str(task.state) for task in run.get_task_instances()}
        if str(run.state) != "success" or not task_states or any(state != "success" for state in task_states.values()):
            raise RuntimeError(f"Airflow execution failed: dag={run.state}, tasks={task_states}")
        report_path = run_path(root, "results", run_id) / "quality_result.json"
        report = read_json(report_path)
        if report["publication_status"] not in {"PUBLISHED", "QUARANTINED"}:
            raise RuntimeError("DAG completed without a publication disposition")
        report.update(pipeline_status="SUCCESS", orchestration_status="SUCCESS", timestamp=now(),
                      execution_mode="airflow_dag_test", airflow_dag_id=dag.dag_id,
                      airflow_run_id=run.run_id, airflow_task_states=task_states)
        write_json(report_path, report)
    except Exception as error:
        execution_failure = {"run_id": run_id, "pipeline_status": "FAILED", "orchestration_status": "FAILED",
                             "error_type": type(error).__name__, "timestamp": now()}
        write_json(run_path(root, "results", run_id) / "execution_failure.json", execution_failure)
        report_path = run_path(root, "results", run_id) / "quality_result.json"
        if report_path.exists():
            report = read_json(report_path)
            report.update(pipeline_status="FAILED", orchestration_status="FAILED", timestamp=now())
            write_json(report_path, report)
        raise
    emit("pipeline_completed", **report)
    print(f"\nRUN ID: {run_id}\n"
          f"ORCHESTRATION STATUS: {report['orchestration_status']}\n"
          f"TRANSFORMATION STATUS: {report['transformation_status']}\n"
          f"DATA QUALITY STATUS: {report['data_quality_status']}\n"
          f"PUBLICATION STATUS: {report['publication_status']}\n"
          f"RECORDS EXPECTED: {report['records_expected']:,}\n"
          f"RECORDS RECEIVED: {report['records_received']:,}\n"
          f"COMPLETENESS: {report['completeness_percentage']:.2f}%\n"
          f"QUALITY RESULT: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=["healthy", "incomplete-source"])
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--data-root", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--contract", type=Path, default=PROJECT_ROOT / "config/data_contract.yaml")
    args = parser.parse_args()
    execute(args.scenario, args.data_root, args.contract, args.run_id or f"{args.scenario}-{uuid4().hex[:12]}")


if __name__ == "__main__":
    main()
