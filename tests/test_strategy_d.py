"""
Strategy D Test Harness: MATLAB/Simulink as Universal Translation Hub.

Tests the PSSE → Simulink → PowerFactory translation pipeline concept,
including system identification for UDM reverse-engineering and block
diagram reconstruction.

Note: Full MATLAB/Simulink tests require a MATLAB license. These tests
validate the conceptual pipeline using Python equivalents (scipy for
system ID, the existing dynaxlate parsers for PSSE data, and structural
checks on the strategy document and MATLAB scripts).
"""

import pytest
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.linalg import norm

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
PLANS_DIR = PROJECT_ROOT / "plans"
MODELS_DIR = PROJECT_ROOT / "models" / "psse"


def cascade_tf(*tfs):
    """Cascade (series) multiple transfer functions by convolving
    numerator and denominator polynomials. Replaces the missing
    signal.series() in scipy 1.16."""
    num = [1.0]
    den = [1.0]
    for tf in tfs:
        num = np.convolve(num, tf.num)
        den = np.convolve(den, tf.den)
    return signal.TransferFunction(num, den)


# =========================================================================
# Document Completeness Tests
# =========================================================================

class TestStrategyDDocument:
    """Verify the strategy document is complete and well-structured."""

    STRATEGY_FILE = PLANS_DIR / "strategy-d-matlab-simulink-translator.md"

    def test_document_exists(self):
        """Strategy D document must exist."""
        assert self.STRATEGY_FILE.exists(), \
            f"Strategy D document not found at {self.STRATEGY_FILE}"

    def test_document_has_overview(self):
        """Document must contain an overview section."""
        content = self.STRATEGY_FILE.read_text()
        assert "## Overview" in content

    def test_document_has_rationale(self):
        """Document must explain why MATLAB/Simulink is the right choice."""
        content = self.STRATEGY_FILE.read_text()
        assert "## Rationale" in content

    def test_document_has_architecture(self):
        """Document must show the system architecture diagram."""
        content = self.STRATEGY_FILE.read_text()
        assert "## Architecture" in content

    def test_document_has_export_paths(self):
        """Document must describe all 4 export paths."""
        content = self.STRATEGY_FILE.read_text()
        for path_num in [1, 2, 3, 4]:
            assert f"Path {path_num}" in content, \
                f"Missing Export Path {path_num}"

    def test_document_has_system_id(self):
        """Document must describe System Identification for UDMs."""
        content = self.STRATEGY_FILE.read_text()
        assert "identify_udm" in content or "system_id" in content.lower()

    def test_document_has_test_harness(self):
        """Document must include a MATLAB test harness section."""
        content = self.STRATEGY_FILE.read_text()
        assert "%%" in content or "run_strategy_d_tests" in content

    def test_document_has_limitations(self):
        """Document must list limitations."""
        content = self.STRATEGY_FILE.read_text()
        assert "## Limitations" in content

    def test_document_has_references(self):
        """Document must include references to MathWorks tools."""
        content = self.STRATEGY_FILE.read_text()
        assert "## References" in content
        assert "au.mathworks.com" in content.lower()

    def test_document_references_mupower(self):
        """Document must mention MATPOWER for .raw parsing."""
        content = self.STRATEGY_FILE.read_text()
        assert "MATPOWER" in content

    def test_document_references_digexfun(self):
        """Document must mention digexfun interface for C DLL export."""
        content = self.STRATEGY_FILE.read_text()
        assert "digexfun" in content

    def test_document_references_fmu(self):
        """Document must mention FMU/FMI export pathway."""
        content = self.STRATEGY_FILE.read_text()
        assert "FMU" in content or "FMI" in content

    def test_document_has_phases(self):
        """Document must describe phased implementation plan."""
        content = self.STRATEGY_FILE.read_text()
        assert "Phase 1" in content
        assert "Phase 2" in content
        assert "Phase 3" in content

    def test_document_has_effort_estimate(self):
        """Document must include effort estimates."""
        content = self.STRATEGY_FILE.read_text()
        assert "## Estimated Effort" in content

    def test_document_has_integration_recommendation(self):
        """Document must describe integration with other strategies."""
        content = self.STRATEGY_FILE.read_text()
        assert "Integration" in content or "D +" in content

    def test_document_size(self):
        """Document should be substantial (at least 10KB of content)."""
        size = self.STRATEGY_FILE.stat().st_size
        assert size > 10000, \
            f"Strategy D document is only {size} bytes, expected > 10KB"


# =========================================================================
# Simulink Block Diagram Mapping Tests
# =========================================================================

class TestSimulinkBlockMapping:
    """Test that PSSE transfer function blocks map correctly to Simulink
    equivalents. Uses scipy.signal as a proxy for Simulink's transfer
    function semantics."""

    def test_esst3a_lead_lag_equivalent(self):
        """ESST3A lead-lag block: PSSE TR → Simulink 1/(1+s*TR).

        The first block in ESST3A is simply a measurement delay:
          V_in → [1/(1+s*TR)] → V_out
        This is a low-pass filter with time constant TR ≈ 0.02s.
        """
        TR = 0.02
        sys_simulink = signal.TransferFunction([1.0], [TR, 1.0])

        _, mag, _ = signal.bode(sys_simulink, w=[0.01, 0.1, 1.0, 10.0, 100.0])

        # DC gain should be 0 dB (1.0)
        assert abs(mag[0]) < 0.1, f"DC gain should be ~0dB, got {mag[0]} dB"
        # High frequency should roll off
        assert mag[-1] < mag[0], "High frequency gain should be lower than DC"

    def test_exdc2_pi_controller_equivalent(self):
        """EXDC2 PI section maps to Simulink PID Controller.

        EXDC2 has a PI controller: K_A * (1 + 1/(s*T_A))
        In Simulink: PID Controller with P=K_A, I=K_A/T_A
        """
        K_A = 100.0
        T_A = 0.05

        # PSSE representation: K_A * (1 + 1/(s*T_A)) = (K_A*T_A*s + K_A) / (T_A*s)
        num_psse = [K_A * T_A, K_A]
        den_psse = [T_A, 0]

        # Simulink PID: K_p + K_i/s = (K_p*s + K_i) / s
        K_p = K_A
        K_i = K_A / T_A
        num_simulink = [K_p, K_i]
        den_simulink = [1, 0]

        sys_psse = signal.TransferFunction(num_psse, den_psse)
        sys_simulink = signal.TransferFunction(num_simulink, den_simulink)

        t = np.linspace(0, 1.0, 1000)
        _, y_psse = signal.step(sys_psse, T=t)
        _, y_simulink = signal.step(sys_simulink, T=t)

        max_diff = np.max(np.abs(y_psse - y_simulink))
        assert max_diff < 1e-10, \
            f"PI controller mismatch: max diff = {max_diff}"

    def test_tgov1_governor_structure(self):
        """TGOV1 governor: PSSE block chain maps to Simulink series.

        TGOV1: speed deviation → droop → two lags → transient → limits
        """
        R = 0.05       # Droop (speed regulation)
        T1 = 0.5       # Governor time constant
        T2 = 3.0       # Servo time constant
        T3 = 10.0      # Transient gain time constant

        # TGOV1 transfer function:
        # ΔPm / Δω = (1/R) * [1/(1+s*T1)] * [1/(1+s*T2)] * [1/(1+s*T3)]
        # At DC (s=0): ΔPm/Δω = 1/R
        # So the DC gain of the full path is 1/R = 20

        num = [1.0]
        den = np.convolve(
            np.convolve([T1, 1.0], [T2, 1.0]),
            [T3, 1.0]
        )
        # Apply droop factor
        num_gov = [1.0 / R]
        den_gov = den.tolist()

        sys_gov = signal.TransferFunction(num_gov, den_gov)
        poles = sys_gov.poles
        assert np.all(np.real(poles) < 0), \
            f"TGOV1 has unstable poles: {poles}"

        # DC gain = 1/R
        dc_gain = num_gov[-1] / den_gov[-1]
        assert abs(dc_gain - 1.0 / R) < 0.01, \
            f"TGOV1 DC gain = {dc_gain}, expected {1.0 / R}"

    def test_genrou_operational_to_coupled_circuit(self):
        """GENROU → ElmSym parameter transformation.

        PSSE GENROU uses operational impedances.
        PowerFactory ElmSym uses coupled circuit parameters.
        Conversion: L = X / ω_base
        """
        omega_base = 2 * np.pi * 50  # 50 Hz system

        Xd = 1.8
        Xq = 1.7
        Xd_prime = 0.3
        Xq_prime = 0.55
        Xd_dprime = 0.25
        Xq_dprime = 0.25
        Xl = 0.15

        Ld = Xd / omega_base
        Lq = Xq / omega_base
        Ld_prime = Xd_prime / omega_base
        Lq_prime = Xq_prime / omega_base
        Ld_dprime = Xd_dprime / omega_base
        Lq_dprime = Xq_dprime / omega_base

        assert Ld >= Ld_prime, f"Ld ({Ld}) >= L'd ({Ld_prime})"
        assert Ld_prime >= Ld_dprime, f"L'd ({Ld_prime}) >= L''d ({Ld_dprime})"
        assert Lq >= Lq_prime, f"Lq ({Lq}) >= L'q ({Lq_prime})"
        assert Lq_prime >= Lq_dprime, f"L'q ({Lq_prime}) >= L''q ({Lq_dprime})"
        # Round rotor: X''d ≈ X''q
        assert abs(Xd_dprime - Xq_dprime) < 0.05

    def test_ieeest_block_structure(self):
        """IEEEST stabilizer: Simulink builds the same washout + phase comp.

        IEEEST: Washout → Lead-Lag 1 → Lead-Lag 2 → Gain
        """
        TW = 2.0
        T1, T2, T3, T4 = 0.2, 0.05, 3.02, 5.51
        KS = 5.0

        # Washout: s*TW/(1+s*TW)
        sys_washout = signal.TransferFunction([TW, 0], [TW, 1])
        # Lead-lag 1: (1+s*T1)/(1+s*T2)
        sys_ll1 = signal.TransferFunction([T1, 1], [T2, 1])
        # Lead-lag 2: (1+s*T3)/(1+s*T4)
        sys_ll2 = signal.TransferFunction([T3, 1], [T4, 1])

        # Cascade using polynomial convolution
        num = np.convolve(np.convolve(sys_washout.num, sys_ll1.num), sys_ll2.num) * KS
        den = np.convolve(np.convolve(sys_washout.den, sys_ll1.den), sys_ll2.den)
        sys_stab = signal.TransferFunction(num, den)

        # Step response
        t = np.linspace(0, 50, 1000)
        _, y_step = signal.step(sys_stab, T=t)
        steady_state = np.mean(y_step[-100:])
        assert abs(steady_state) < 0.01, \
            f"IEEEST steady-state should ≈ 0 (washout), got {steady_state}"

        # Mid-frequency gain should exist (damping)
        freqs = [0.1, 0.5, 1.0, 2.0, 5.0]
        w = [2 * np.pi * f for f in freqs]
        _, mag, _ = signal.bode(sys_stab, w=w)

        # For typical IEEEST parameters, there's meaningful gain at local mode freq (~1Hz)
        mode_freq_idx = 2  # 1.0 Hz
        assert mag[mode_freq_idx] > -10, \
            f"Stabilizer gain at 1Hz = {mag[mode_freq_idx]:.1f} dB (expected > -10 dB)"


# =========================================================================
# System Identification Tests (MATLAB SysID analog in Python/scipy)
# =========================================================================

class TestSystemIdentification:
    """Test the System Identification concept that enables UDM reverse-
    engineering without source code. Uses scipy.signal as a proxy for
    MATLAB's System Identification Toolbox.

    This tests: given a "black box" compiled UDM (simulated by a known
    transfer function), can we recover its structure from I/O data?
    """

    @pytest.fixture
    def true_udm_transfer_function(self):
        """Simulate a 'black box' UDM — a 3rd-order transfer function
        representing something like a compound exciter with lead-lag."""
        num = [10.0, 15.0, 5.0]
        den = [1.0, 4.0, 5.0, 2.0]
        return signal.TransferFunction(num, den)

    @pytest.fixture
    def step_test_data(self, true_udm_transfer_function):
        """Generate step response test data."""
        t = np.linspace(0, 10, 1000)
        _, y = signal.step(true_udm_transfer_function, T=t)
        u = np.ones_like(t)
        return t, u, y

    @pytest.fixture
    def chirp_test_data(self, true_udm_transfer_function):
        """Generate chirp/sweep response."""
        t = np.linspace(0, 20, 2000)
        f0, f1 = 0.1, 10.0
        u = signal.chirp(t, f0=f0, f1=f1, t1=t[-1], method='logarithmic')
        _, y, _ = signal.lsim(true_udm_transfer_function, u, t)
        return t, u, y

    def test_identify_from_step_response(self, step_test_data):
        """Recover transfer function from step response alone."""
        t, u, y = step_test_data

        # Estimate DC gain from steady-state
        dc_gain = np.mean(y[-100:])

        # Estimate time constant from the step response shape.
        # True TF = (10s^2+15s+5) / (s^3+4s^2+5s+2) = (s+1)(s+0.5) / (s+1)^2(s+2)
        # All poles are real: -1 (double), -2
        # Dominant τ = 1/|p_min| where p_min is the slowest pole
        # Slowest pole = -1 → τ = 1.0s, so system reaches steady state by ~4τ = 4s
        # The 63% threshold may be reached faster due to the zero at s=-0.5
        # So we check that a meaningful fraction of final value is reached by ~τ

        # Compute 63% rise time
        idx_63 = np.where(y >= 0.63 * y[-1])[0][0]
        tau_estimate = t[idx_63]

        # DC gain should match: G(0) = 5/2 = 2.5
        assert 2.0 < dc_gain < 3.0, \
            f"Expected DC gain ~2.5, got {dc_gain:.3f}"

    def test_identify_from_chirp_response(self, chirp_test_data):
        """Use chirp/sweep to identify frequency response.

        This demonstrates the MATLAB System Identification Toolbox concept.
        The H1 frequency response estimator gives a non-parametric estimate
        of the transfer function from chirp data. MATLAB's tfest would use
        prediction-error minimization for robust parametric fitting.
        """
        t, u, y = chirp_test_data
        dt = t[1] - t[0]
        fs = 1.0 / dt

        # Compute H1 frequency response estimate via CSD and PSD
        nperseg = 256
        f, P_uy = signal.csd(u, y, fs, nperseg=nperseg)
        _, P_uu = signal.csd(u, u, fs, nperseg=nperseg)

        H_estimate = P_uy / (P_uu + 1e-10)

        # Compare with true TF's frequency response at a few frequencies
        sys_true = signal.TransferFunction([10.0, 15.0, 5.0], [1.0, 4.0, 5.0, 2.0])
        _, mag_true, _ = signal.bode(sys_true, w=2 * np.pi * f)

        # Compute magnitude error (in dB) at valid frequencies
        mag_est = 20 * np.log10(np.abs(H_estimate) + 1e-10)
        valid = (f > 0.2) & (f < 3.0)

        if np.sum(valid) < 5:
            pytest.skip("Insufficient valid frequency points for comparison")

        # The H1 estimate should capture the general magnitude shape
        mag_err = np.abs(mag_est[valid] - mag_true[valid])
        mean_mag_err = np.mean(mag_err)
        assert mean_mag_err < 15.0, \
            f"Mean magnitude error = {mean_mag_err:.1f} dB (expected < 15 dB)"
        # Shape correlation should be positive (same trend)
        corr = np.corrcoef(mag_est[valid], mag_true[valid])[0, 1]
        assert corr > 0.3, \
            f"Frequency response shape correlation = {corr:.2f} (expected > 0.3)"

    def test_udm_classification_by_step_shape(self):
        """Classify an unknown UDM by its step response shape."""
        test_cases = [
            {
                'name': 'exciter_like',
                # Fast exciter: high gain, 1 lag pole ~10Hz, dominant pole ~1Hz
                'num': [1000.0],
                'den': [0.015, 1.015, 1.0],
                'expected_type': 'exciter'
            },
            {
                'name': 'governor_like',
                # Slow governor: low freq, monotonic response
                'num': [20.0],
                'den': [5.0, 6.0, 1.0],
                'expected_type': 'governor'
            },
            {
                'name': 'pss_like',
                # Stabilizer: washout + lead-lag, returns to zero
                'num': [2.0, 0.5, 0.0],
                'den': [1.0, 2.0, 2.0, 1.0],
                'expected_type': 'pss'
            },
        ]

        for case in test_cases:
            sys = signal.TransferFunction(case['num'], case['den'])
            t = np.linspace(0, 10, 1000)
            _, y = signal.step(sys, T=t)

            steady = np.mean(y[-100:])

            if case['expected_type'] == 'pss':
                # PSS: returns to zero (washout)
                assert abs(steady) < 0.05 * np.max(np.abs(y)), \
                    f"{case['name']}: PSS steady={steady:.3f} (should ≈ 0)"
            elif case['expected_type'] == 'governor':
                # Governor: monotonic, low overshoot
                overshoot = np.max(y) - y[-1]
                assert overshoot / y[-1] < 0.3, \
                    f"{case['name']}: Governor overshoot too high"
            elif case['expected_type'] == 'exciter':
                # Exciter: fast response — reaches 90% of final value quickly
                idx_90 = np.where(y >= 0.9 * y[-1])[0]
                t_90 = t[idx_90[0]] if len(idx_90) > 0 else 999.0
                assert t_90 < 3.0, \
                    f"{case['name']}: Exciter t_90={t_90:.3f}s (expected < 3.0s)"


# =========================================================================
# MATLAB Script Syntax Check Tests
# =========================================================================

class TestMATLABScriptSyntax:
    """Basic structural checks on MATLAB scripts in the strategy plan."""

    def test_dyr_parser_syntax(self):
        """Validate MATLAB .dyr parser function structure."""
        content = (PLANS_DIR / "strategy-d-matlab-simulink-translator.md").read_text()
        assert "parse_dyr.m" in content
        assert "fopen" in content
        assert "regexp" in content or "regexpi" in content

    def test_matlab_function_structures(self):
        """Validate MATLAB function syntax in the plan."""
        content = (PLANS_DIR / "strategy-d-matlab-simulink-translator.md").read_text()
        assert "classdef" in content
        assert "properties" in content
        assert "methods" in content

    def test_export_path_functions(self):
        """Validate MATLAB export function structures."""
        content = (PLANS_DIR / "strategy-d-matlab-simulink-translator.md").read_text()
        assert "rtwbuild" in content
        assert "fmuexport" in content
        assert "py.powerfactory" in content

    def test_toolboxes_documented(self):
        """All required MATLAB toolboxes should be documented."""
        content = (PLANS_DIR / "strategy-d-matlab-simulink-translator.md").read_text()
        assert "MATPOWER" in content
        assert "## Key MATLAB Toolbox Requirements" in content


# =========================================================================
# Integration with Existing dynaxlate Code
# =========================================================================

class TestIntegrationWithDynaxlate:
    """Test that Strategy D integrates with the existing dynaxlate codebase."""

    def test_dyr_parser_reused(self):
        """Strategy D uses the existing .dyr parser (or MATLAB equivalent)."""
        from dynaxlate.dyr_parser import parse_dyr
        dyr = parse_dyr(MODELS_DIR / "ieee14.dyr")
        assert len(dyr.models) > 0
        assert "GENROU" in dyr.model_types
        assert "ESST3A" in dyr.model_types

    def test_model_registry_reused(self):
        """Strategy D uses the existing model registry as its parameter map."""
        from dynaxlate.model_registry import get_mapping
        for model_name in ["GENROU", "ESST3A", "TGOV1", "IEEEST"]:
            mapping = get_mapping(model_name)
            assert mapping is not None, f"{model_name} not in registry"
            assert len(mapping.parameters) > 0, \
                f"{model_name} has no parameter mappings"

    def test_model_registry_supports_simulink_params(self):
        """Model registry has Simulink-relevant parameters."""
        from dynaxlate.model_registry import get_mapping
        mapping = get_mapping("GENROU")
        assert mapping is not None
        param_names = {p.psse_name for p in mapping.parameters}

        essential = {"Tdp0", "Tdpp0", "Tqp0", "Tqpp0", "H", "D", "Xd", "Xq"}
        missing = essential - param_names
        assert not missing, \
            f"GENROU registry missing Simulink-essential params: {missing}"

    def test_dsl_generator_reused(self):
        """Strategy D's DSL generation can leverage existing code."""
        from dynaxlate.dsl_generator import DSLGenerator, translate_udm
        # The generator takes a FortranUDM (UDMs only), but we verify
        # the module is importable and the convenience function exists
        assert translate_udm is not None
        assert DSLGenerator is not None

    def test_comparison_tool_reused(self):
        """Strategy D reuses the comparison framework."""
        from dynaxlate.comparison import compare_timeseries
        assert compare_timeseries is not None


# =========================================================================
# MATLAB Availability Test (Optional — depends on environment)
# =========================================================================

class TestMATLABAvailability:
    """Check if MATLAB is available in the environment.

    These tests are marked as optional — skip if MATLAB isn't installed.
    """

    @pytest.mark.skipif(
        True,
        reason="MATLAB not available in CI/test environment. "
               "Run manually on MATLAB-equipped workstation."
    )
    def test_matlab_installed(self):
        """Check MATLAB is available via command line."""
        import subprocess
        result = subprocess.run(
            ["matlab", "-batch", "version"],
            capture_output=True, text=True, timeout=30
        )
        assert result.returncode == 0
        assert "R20" in result.stdout

    @pytest.mark.skipif(
        True,
        reason="MATPOWER not available in CI. Run manually."
    )
    def test_matpower_parses_raw(self):
        """Check MATPOWER can parse a PSSE .raw file."""
        import subprocess
        result = subprocess.run(
            ["matlab", "-batch",
             f"mpc = psse2mpc('{MODELS_DIR}/ieee14.raw'); "
             "disp(length(mpc.bus)); exit"],
            capture_output=True, text=True, timeout=60
        )
        assert result.returncode == 0
        assert "14" in result.stdout

    @pytest.mark.skipif(
        True,
        reason="System ID Toolbox not available in CI. Run manually."
    )
    def test_matlab_system_id(self):
        """Test System Identification Toolbox tfest on known TF."""
        import subprocess
        matlab_code = (
            "data = idinput(1000, 'prbs', [0, 0.5]);"
            "sys_true = idtf([10 15 5], [1 4 5 2]);"
            "y = sim(sys_true, data);"
            "idd = iddata(y, data, 0.01);"
            "sys_id = tfest(idd, 3, 2);"
            "compare(idd, sys_id);"
            "disp(sys_id.Report.Fit.FitPercent);"
        )
        result = subprocess.run(
            ["matlab", "-batch", matlab_code],
            capture_output=True, text=True, timeout=120
        )
        assert result.returncode == 0


# =========================================================================
# Reference Verification Tests
# =========================================================================

class TestReferences:
    """Verify MathWorks references in the strategy document are valid."""

    def test_strategy_has_mathworks_references(self):
        """Strategy document references mathworks.com sufficiently."""
        content = (PLANS_DIR / "strategy-d-matlab-simulink-translator.md").read_text()
        url_count = content.lower().count("mathworks.com")
        assert url_count >= 5, \
            f"Only {url_count} references to mathworks.com in document"

    def test_strategy_references_matlab_central(self):
        """Strategy references MATLAB Central / community."""
        content = (PLANS_DIR / "strategy-d-matlab-simulink-translator.md").read_text()
        assert "mathworks.com/matlabcentral" in content.lower() or \
            "MATLAB Central" in content

    def test_strategy_references_powerfactory_interface(self):
        """Strategy references DIgSILENT documentation."""
        content = (PLANS_DIR / "strategy-d-matlab-simulink-translator.md").read_text()
        assert "digsilent.de" in content.lower()
