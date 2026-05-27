"""
Strategy A Test Harness: Native PowerFactory Import + Post-Processing.

Tests the PSSE → PowerFactory native import path with automated
corrections and verification.
"""

import pytest
from pathlib import Path
import numpy as np

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models" / "psse"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)


class TestPSSEBaseline:
    """Test PSSE baseline simulation via ANDES."""

    @pytest.fixture
    def kundur_raw(self):
        return MODELS_DIR / "kundur.raw"

    @pytest.fixture
    def kundur_dyr(self):
        return MODELS_DIR / "kundur_full.dyr"

    @pytest.fixture
    def ieee14_raw(self):
        return MODELS_DIR / "ieee14.raw"

    @pytest.fixture
    def ieee14_dyr(self):
        return MODELS_DIR / "ieee14.dyr"

    def test_andes_loads_raw(self, kundur_raw):
        """ANDES successfully loads .raw power flow file."""
        import andes
        ss = andes.load(str(kundur_raw), no_output=True, quiet=True)
        assert ss is not None
        assert ss.Bus.n > 0
        assert ss.Line.n > 0

    def test_andes_loads_dyr(self, kundur_raw, kundur_dyr):
        """ANDES successfully loads .dyr with standard models."""
        import andes
        ss = andes.load(str(kundur_raw), addfile=str(kundur_dyr),
                        no_output=True, quiet=True)
        assert ss is not None
        # Should have dynamic models loaded (GENROU, EXDC2, TGOV1)
        assert ss.GENROU.n > 0, "No GENROU models loaded"
        assert ss.EXDC2.n > 0, "No EXDC2 models loaded"
        assert ss.TGOV1.n > 0, "No TGOV1 models loaded"

    def test_power_flow_converges(self, kundur_raw):
        """Power flow converges on the test case."""
        import andes
        ss = andes.run(str(kundur_raw), no_output=True, quiet=True)
        # ANDES returns after PFlow
        assert ss.PFlow.converged

    def test_power_flow_results_reasonable(self, ieee14_raw):
        """Power flow produces physically reasonable results."""
        import andes
        ss = andes.run(str(ieee14_raw), no_output=True, quiet=True)
        # ANDES stores voltage magnitudes in dae.y after angles
        # For n buses: dae.y[:n] = angles (rad), dae.y[n:2n] = voltage magnitudes (pu)
        n_bus = ss.Bus.n
        vm = ss.dae.y[n_bus:2*n_bus]
        # All bus voltages should be between 0.9 and 1.2 pu
        assert np.all(vm >= 0.85), f"Low voltage buses: {vm[vm < 0.85]}"
        assert np.all(vm <= 1.15), f"High voltage buses: {vm[vm > 1.15]}"


class TestDYRParser:
    """Test the standalone .dyr file parser."""

    @pytest.fixture
    def kundur_dyr(self):
        from dynaxlate.dyr_parser import parse_dyr
        return parse_dyr(MODELS_DIR / "kundur_full.dyr")

    @pytest.fixture
    def ieee14_dyr(self):
        from dynaxlate.dyr_parser import parse_dyr
        return parse_dyr(MODELS_DIR / "ieee14.dyr")

    def test_parser_extracts_models(self, kundur_dyr):
        """Parser extracts all model entries from .dyr file."""
        assert len(kundur_dyr.models) > 0
        assert "GENROU" in kundur_dyr.model_types

    def test_parser_identifies_model_types(self, kundur_dyr):
        """Parser correctly identifies all model types."""
        expected = {"GENROU", "EXDC2", "TGOV1"}
        assert expected.issubset(kundur_dyr.model_types), \
            f"Missing models: {expected - kundur_dyr.model_types}"

    def test_ieee14_model_types(self, ieee14_dyr):
        """IEEE 14-bus .dyr has expected model types."""
        expected = {"GENROU", "ESST3A", "TGOV1"}
        assert expected.issubset(ieee14_dyr.model_types), \
            f"Missing models: {expected - ieee14_dyr.model_types}"

    def test_model_parameters_parsed(self, kundur_dyr):
        """Parameters are correctly extracted from model entries."""
        genrou_models = kundur_dyr.get_models_by_type("GENROU")
        assert len(genrou_models) >= 4  # Kundur has 4 generators
        # First GENROU should have inertia (H) as first param
        first = genrou_models[0]
        assert len(first.parameters) >= 4
        assert first.parameters[0] == 8.0  # H = 8.0 for bus 1

    def test_bus_model_map(self, kundur_dyr):
        """Bus-to-model mapping is correct."""
        bus_map = kundur_dyr.get_bus_model_map()
        assert 1 in bus_map  # Bus 1 should have dynamics
        assert "GENROU" in bus_map[1]

    def test_summary(self, kundur_dyr):
        """Summary statistics are correct."""
        summary = kundur_dyr.summary()
        assert summary["total_entries"] > 0
        assert len(summary["model_types"]) > 0
        assert "GENROU" in summary["model_counts"]


class TestModelRegistry:
    """Test the PSSE ↔ PowerFactory model registry."""

    def test_registry_has_standard_models(self):
        """Registry contains all standard PSSE models from test files."""
        from dynaxlate.model_registry import list_supported_models
        models = list_supported_models()
        expected = ["GENROU", "GENCLS", "ESST3A", "EXDC2", "TGOV1", "IEEEG1", "IEEEST", "ST2CUT"]
        for m in expected:
            assert m in models, f"Model {m} missing from registry"

    def test_genrou_mapping(self):
        """GENROU has complete parameter mapping."""
        from dynaxlate.model_registry import get_mapping
        mapping = get_mapping("GENROU")
        assert mapping is not None
        assert mapping.pf_model_class == "ElmSym"
        assert len(mapping.parameters) >= 10
        # Check key parameters
        param_names = [p.psse_name for p in mapping.parameters]
        assert "H" in param_names
        assert "D" in param_names
        assert "Xd" in param_names

    def test_parameter_transform(self):
        """Parameter transformation produces correct values."""
        from dynaxlate.model_registry import get_mapping
        mapping = get_mapping("GENROU")
        psse_values = {"H": 8.0, "D": 0.03, "Xd": 1.8}
        pf_values = mapping.apply(psse_values)
        assert pf_values["H"] == 8.0
        assert pf_values["D"] == 0.03
        assert pf_values["xd"] == 1.8

    def test_damping_correction_flagged(self):
        """Damping constant correction is flagged."""
        from dynaxlate.model_registry import get_mapping
        mapping = get_mapping("GENROU")
        assert any("Damping" in c or "damping" in c.lower()
                    for c in mapping.corrections)

    def test_saturation_correction_flagged(self):
        """Saturation model difference is flagged."""
        from dynaxlate.model_registry import get_mapping
        mapping = get_mapping("GENROU")
        assert any("Saturation" in c or "saturation" in c.lower()
                    for c in mapping.corrections)


class TestComparisonFramework:
    """Test the comparison/verification framework."""

    def test_identical_signals_pass(self):
        """Identical time-series pass comparison."""
        from dynaxlate.comparison import compare_timeseries
        t = np.arange(0, 10, 0.01)
        v = np.sin(2 * np.pi * 50 * t)
        metric = compare_timeseries(t, v, t, v, tolerance=0.01,
                                     required_pct=95.0, variable_name="test")
        assert metric.passes
        assert metric.rmse < 1e-10

    def test_different_signals_fail(self):
        """Significantly different signals fail comparison."""
        from dynaxlate.comparison import compare_timeseries
        t = np.arange(0, 10, 0.01)
        v1 = np.ones_like(t)
        v2 = np.ones_like(t) + 0.1  # 0.1 pu offset
        metric = compare_timeseries(t, v1, t, v2, tolerance=0.01,
                                     required_pct=95.0, variable_name="test")
        assert not metric.passes

    def test_powerflow_comparison(self):
        """Power flow comparison works with synthetic data."""
        from dynaxlate.comparison import compare_powerflow
        vm1 = np.array([1.05, 1.03, 1.01, 0.98, 1.02])
        va1 = np.array([0.0, -2.5, -5.1, -8.3, -3.7])
        vm2 = np.array([1.049, 1.031, 1.009, 0.981, 1.019])
        va2 = np.array([0.0, -2.4, -5.0, -8.2, -3.6])
        metrics = compare_powerflow(vm1, va1, vm2, va2)
        assert len(metrics) == 2
        # Should pass with tight tolerance
        assert all(m.passes for m in metrics)


class TestPowerFactoryAdapter:
    """Test PowerFactory adapter (mocked, since PF may not be installed)."""

    def test_adapter_instantiation(self):
        """Adapter can be instantiated without PowerFactory."""
        from dynaxlate.pf_adapter import PowerFactoryAdapter
        adapter = PowerFactoryAdapter()
        assert adapter.app is None
        assert not adapter._connected

    def test_connect_without_pf_returns_false(self):
        """Connection fails gracefully when PowerFactory is not installed."""
        from dynaxlate.pf_adapter import PowerFactoryAdapter
        adapter = PowerFactoryAdapter()
        # This should not raise — it should return False gracefully
        result = adapter.connect()
        assert result is False

    def test_context_manager(self):
        """Context manager works even without PowerFactory."""
        from dynaxlate.pf_adapter import PowerFactoryAdapter
        adapter = PowerFactoryAdapter()
        # Should not raise
        with adapter:
            pass
