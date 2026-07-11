import pytest

from healthchain.pipeline import Pipeline


@pytest.fixture
def cds_fhir_adapter():
    from healthchain.io import CdsFhirAdapter

    return CdsFhirAdapter(hook_name="patient-view")


@pytest.fixture
def mock_basic_pipeline():
    return Pipeline()
