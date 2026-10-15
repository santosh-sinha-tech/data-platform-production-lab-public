"""Validate configuration before handling any data; invalid contracts fail closed."""

import math
from pathlib import Path

import yaml

FIELDS = {"booking_id", "customer_id", "booking_timestamp", "origin", "destination",
          "booking_amount", "currency", "booking_status"}


def validate_contract(contract):
    if contract["contract_version"] != 1 or contract["dataset"] != "daily_bookings":
        raise ValueError("Unsupported contract")
    expected = contract["expected_volume"]
    if type(expected) is not int or expected <= 0:
        raise ValueError("expected_volume must be a positive integer")
    fields = contract["mandatory_fields"]
    if not fields or len(set(fields)) != len(fields) or not set(fields) <= FIELDS:
        raise ValueError("mandatory_fields must be unique supported booking fields")
    if contract["currency"] != "USD" or contract["reconciliation"]["field"] != "booking_amount":
        raise ValueError("V1 supports USD booking_amount reconciliation only")

    def number(value):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("Thresholds must be finite numbers")
        return value

    minimum, target, maximum = [number(contract[key]) for key in (
        "minimum_volume_percentage", "pass_volume_percentage", "maximum_volume_percentage")]
    if not 0 < minimum <= target <= maximum or target != 100:
        raise ValueError("Volume thresholds must satisfy 0 < minimum <= 100 <= maximum")
    if not 0 <= number(contract["warning_null_percentage"]) <= number(contract["maximum_null_percentage"]) <= 100:
        raise ValueError("Invalid null thresholds")
    reconciliation = contract["reconciliation"]
    if not 0 <= number(reconciliation["warning_tolerance_percentage"]) <= number(reconciliation["tolerance_percentage"]):
        raise ValueError("Invalid reconciliation tolerances")
    return contract


def load_contract(path):
    return validate_contract(yaml.safe_load(Path(path).read_text()))
