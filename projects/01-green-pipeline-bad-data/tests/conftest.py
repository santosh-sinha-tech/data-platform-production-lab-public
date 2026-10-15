from pathlib import Path

import pytest
import yaml

from booking_pipeline.runtime import spark_session


@pytest.fixture(scope="session")
def spark():
    session = spark_session()
    yield session
    session.stop()


@pytest.fixture
def contract_path(tmp_path):
    contract = yaml.safe_load((Path(__file__).parents[1] / "config/data_contract.yaml").read_text())
    # Behaviour tests stay fast; the two CLI experiments exercise full volumes.
    contract["expected_volume"] = 1000
    path = tmp_path / "contract.yaml"
    path.write_text(yaml.safe_dump(contract))
    return path
