"""Offline acceptance checks: invalid traces cannot imply equivalence."""

import numpy as np
import pytest

from dynaxlate.comparison import compare_timeseries
from dynaxlate.pf_adapter import PowerFactoryAdapter


@pytest.mark.parametrize("connected", [False, True])
def test_rms_stub_never_reports_success(connected):
    adapter = PowerFactoryAdapter()
    adapter._connected = connected
    adapter.app = object()  # No simulator or connection is needed.
    result = adapter.run_rms_simulation(fault_bus=1)
    assert result["success"] is False
    assert result["error"]


@pytest.mark.parametrize("side", ["reference", "test"])
@pytest.mark.parametrize("time,values", [
    ([], []),
    ([0, 1, 2, 3], [1, 1, 1]),
    ([0, 1, 2, 3], [1, np.nan, 1, 1]),
    ([0, 1, 2, 3], [1, np.inf, 1, 1]),
    ([0, 1, np.nan, 3], [1, 1, 1, 1]),
    ([0, 1, 2, np.inf], [1, 1, 1, 1]),
    ([0, 1, 1, 3], [1, 1, 1, 1]),
    ([3, 2, 1, 0], [1, 1, 1, 1]),
    ([0, 1, 2], [1, 1, 1]),
    ([[0, 1, 2, 3]], [[1, 1, 1, 1]]),
    ([1, 2, 3, 4], [1, 1, 1, 1]),
])
def test_invalid_trace_is_rejected(side, time, values):
    valid = (np.arange(4.0), np.ones(4))
    invalid = (np.asarray(time), np.asarray(values))
    ref, test = (invalid, valid) if side == "reference" else (valid, invalid)
    with pytest.raises(ValueError):
        compare_timeseries(*ref, *test, tolerance=0.01)


@pytest.mark.parametrize("kwargs", [
    {"common_dt": 0}, {"common_dt": -1}, {"common_dt": np.nan},
    {"common_dt": np.inf}, {"tolerance": -1}, {"tolerance": np.inf},
    {"required_pct": 0}, {"required_pct": 101}, {"required_pct": np.nan},
])
def test_invalid_comparison_settings_are_rejected(kwargs):
    settings = {"tolerance": 0.01, **kwargs}
    with pytest.raises(ValueError):
        compare_timeseries(np.arange(4.0), np.ones(4),
                           np.arange(4.0), np.ones(4), **settings)


def test_valid_different_sampling_grids_remain_supported():
    ref = np.linspace(0, 3, 7)
    test = np.linspace(0, 3, 13)
    metric = compare_timeseries(ref, ref**2, test, test**2, tolerance=1e-10)
    assert metric.passes
    assert np.isfinite(metric.rmse)
