"""Deterministic synthetic bookings and independent pre-delivery controls."""

from booking_pipeline.contract import load_contract
from booking_pipeline.observability import emit, write_json
from booking_pipeline.runtime import run_path


def generate(spark, root, run_id, scenario, contract_path):
    if scenario not in {"healthy", "incomplete-source"}:
        raise ValueError("Unknown scenario")
    contract = load_contract(contract_path)
    expected = contract["expected_volume"]
    received = expected if scenario == "healthy" else expected * 82 // 100
    incoming = run_path(root, "incoming", run_id)
    # Every attempt has a new identity. Never overwrite a prior trusted partition.
    for area in ("incoming", "processed", "published", "quarantine", "results", "staging"):
        if run_path(root, area, run_id).exists():
            raise FileExistsError(f"Run already exists: {run_id}; choose a new run_id")

    # Calculated from the FULL population, before delivery is reduced.
    total_cents = sum(10000 + (i * 37) % 90000 for i in range(expected))
    bookings = spark.range(received).selectExpr(
        "concat('B', lpad(cast(id as string), 9, '0')) as booking_id",
        "concat('C', lpad(cast(id % 25000 as string), 6, '0')) as customer_id",
        "timestamp_seconds(1767225600 + (id % 86400)) as booking_timestamp",
        "element_at(array('LHR','DEL','SIN','JFK'), cast(id % 4 + 1 as int)) as origin",
        "element_at(array('DEL','SIN','JFK','LHR'), cast(id % 4 + 1 as int)) as destination",
        "cast((10000 + (id * 37) % 90000) / 100.0 as decimal(18,2)) as booking_amount",
        "'usd' as currency",
        "'confirmed' as booking_status",
    )
    bookings.write.mode("errorifexists").parquet(str(incoming / "bookings"))
    manifest = {
        "run_id": run_id,
        "scenario": scenario,
        "business_date": "2026-01-01",
        "workload": "Synthetic / Illustrative",
        "records_expected": expected,
        "expected_booking_amount": f"{total_cents // 100}.{total_cents % 100:02d}",
        "currency": contract["currency"],
        "control_basis": "Full source population before delivery loss",
        "contract": contract,
    }
    write_json(incoming / "control.json", manifest)
    emit("source_delivered", run_id=run_id, scenario=scenario,
         records_expected=expected, records_received=received)
    return run_id
