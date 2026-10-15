import pytest
import yaml

from booking_pipeline.contract import load_contract
from booking_pipeline.runtime import run_path


@pytest.mark.parametrize("key,value", [("expected_volume", 0), ("expected_volume", True),
                                       ("minimum_volume_percentage", 101), ("maximum_null_percentage", -1),
                                       ("mandatory_fields", ["unsupported"]), ("warning_null_percentage", float("nan"))])
def test_invalid_contract_is_rejected(contract_path, key, value):
    config = yaml.safe_load(contract_path.read_text())
    config[key] = value
    contract_path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError):
        load_contract(contract_path)


def test_run_identity_cannot_escape_data_root(tmp_path):
    with pytest.raises(ValueError, match="run_id"):
        run_path(tmp_path, "published", "../escape")
