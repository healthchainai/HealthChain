import pytest

import healthchain.io as io
import healthchain.io.containers as containers


IO_REMOVED_NAMES = [
    "DataContainer",
    "Dataset",
    "FeatureSchema",
    "FHIRFeatureMapper",
    "BaseMapper",
    "bundle_to_dataframe",
    "TimeWindow",
    "ValidationResult",
]

CONTAINERS_REMOVED_NAMES = ["DataContainer", "Dataset", "FeatureSchema"]


@pytest.mark.parametrize("name", IO_REMOVED_NAMES)
def test_io_tombstone_raises_guiding_import_error(name):
    """Names removed in 0.16.0 raise a guiding ImportError, not a bare AttributeError."""
    with pytest.raises(ImportError, match="removed in 0.16.0"):
        getattr(io, name)


@pytest.mark.parametrize("name", CONTAINERS_REMOVED_NAMES)
def test_containers_tombstone_raises_guiding_import_error(name):
    """Names historically importable from healthchain.io.containers are tombstoned too."""
    with pytest.raises(ImportError, match="removed in 0.16.0"):
        getattr(containers, name)


def test_unknown_attribute_still_raises_attribute_error():
    with pytest.raises(AttributeError):
        io.NotARealName


def test_core_io_imports_still_work():
    """The io module's non-CDA public surface must not require the cda extra."""
    from healthchain.io import Document, BaseAdapter, CdsFhirAdapter

    assert Document is not None
    assert BaseAdapter is not None
    assert CdsFhirAdapter is not None


def test_cda_adapter_importable_when_extra_installed():
    """CdaAdapter resolves normally when the cda extra's deps are present."""
    from healthchain.io import CdaAdapter

    assert CdaAdapter.__name__ == "CdaAdapter"

    from healthchain.io.adapters import CdaAdapter as CdaAdapterFromAdapters

    assert CdaAdapterFromAdapters is CdaAdapter
