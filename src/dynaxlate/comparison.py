"""
Comparison Framework: Compare simulation results between PSSE and PowerFactory.

Implements the verification methodology from the strategy plans,
incorporating critique recommendations:
1. Parameter-level verification
2. Power flow verification
3. Initial condition verification
4. Eigenvalue verification (small-signal)
5. Time-domain verification (large-signal)

Time-domain comparisons validate supplied scalar traces only; they do not
execute simulators or establish matched units, events, or initial conditions.
Cubic interpolation supports finite, strictly increasing one-dimensional time
arrays with at least four samples and matching value lengths. Both traces must
cover the same start/end times; sampling rates may differ. Invalid inputs raise
ValueError rather than producing a partial or misleading passing comparison.
"""

import numpy as np
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Tolerance:
    """Verification tolerance specification."""
    name: str
    value: float
    unit: str
    percentage: float = 0.0  # trajectory percentage required


# Default tolerances per critique recommendations (tightened from original plans)
DEFAULT_TOLERANCES = {
    "powerflow_vm": Tolerance("V magnitude (PF)", 0.005, "pu", 95.0),
    "powerflow_va": Tolerance("V angle (PF)", 0.5, "deg", 95.0),
    "dynamic_vm": Tolerance("V magnitude (dynamic)", 0.01, "pu", 95.0),
    "dynamic_angle": Tolerance("Rotor angle (dynamic)", 3.0, "deg", 98.0),
    "dynamic_freq": Tolerance("Frequency (dynamic)", 0.05, "Hz", 98.0),
    "eigenvalue_real": Tolerance("Eigenvalue (real part)", 0.1, "1/s", 95.0),
    "eigenvalue_imag": Tolerance("Eigenvalue (imag part)", 0.1, "rad/s", 95.0),
    "parameter": Tolerance("Parameter value", 0.001, "pu", 100.0),
}


@dataclass
class ComparisonMetric:
    """Result of comparing two time-series."""
    variable_name: str
    rmse: float
    max_error: float
    mean_error: float
    time_of_max_error: float
    pct_within_tolerance: float
    tolerance: float
    passes: bool


@dataclass
class ComparisonReport:
    """Full comparison report between PSSE and PowerFactory results."""
    name: str
    powerflow_metrics: list[ComparisonMetric] = field(default_factory=list)
    dynamic_metrics: list[ComparisonMetric] = field(default_factory=list)
    eigenvalue_metrics: list[ComparisonMetric] = field(default_factory=list)
    parameter_metrics: list[ComparisonMetric] = field(default_factory=list)
    overall_pass: bool = False

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [f"=== Comparison Report: {self.name} ==="]
        lines.append(f"Overall: {'PASS ✓' if self.overall_pass else 'FAIL ✗'}")
        lines.append("")

        for category, metrics in [
            ("Parameter", self.parameter_metrics),
            ("Power Flow", self.powerflow_metrics),
            ("Eigenvalue", self.eigenvalue_metrics),
            ("Dynamic", self.dynamic_metrics),
        ]:
            if not metrics:
                continue
            lines.append(f"--- {category} ---")
            for m in metrics:
                status = "✓" if m.passes else "✗"
                lines.append(
                    f"  {status} {m.variable_name}: "
                    f"RMSE={m.rmse:.6f}, Max={m.max_error:.6f} at t={m.time_of_max_error:.3f}s, "
                    f"Within tol={m.pct_within_tolerance:.1f}%"
                )
            lines.append("")

        return "\n".join(lines)


def compare_timeseries(
    time_ref: np.ndarray,
    values_ref: np.ndarray,
    time_test: np.ndarray,
    values_test: np.ndarray,
    tolerance: float,
    required_pct: float = 95.0,
    variable_name: str = "unknown",
    common_dt: float = 0.01,
) -> ComparisonMetric:
    """Compare two time-series on a common time grid.

    Uses cubic spline interpolation to align time points.
    """
    from scipy.interpolate import interp1d

    time_ref, values_ref, time_test, values_test = (
        np.asarray(array, dtype=float)
        for array in (time_ref, values_ref, time_test, values_test)
    )
    for label, time, values in (
        ("reference", time_ref, values_ref), ("test", time_test, values_test)
    ):
        if time.ndim != 1 or values.ndim != 1 or time.shape != values.shape:
            raise ValueError(f"{label} time and values must be matching 1-D arrays")
        if time.size < 4:
            raise ValueError(f"{label} trace requires at least four samples")
        if not np.all(np.isfinite(time)) or not np.all(np.isfinite(values)):
            raise ValueError(f"{label} trace must contain only finite samples")
        if not np.all(np.diff(time) > 0):
            raise ValueError(f"{label} time must be strictly increasing")
    if time_ref[0] != time_test[0] or time_ref[-1] != time_test[-1]:
        raise ValueError("Traces must cover the same time interval")
    if not np.isfinite(common_dt) or common_dt <= 0:
        raise ValueError("common_dt must be finite and positive")
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and non-negative")
    if not np.isfinite(required_pct) or not 0 < required_pct <= 100:
        raise ValueError("required_pct must be finite and in (0, 100]")

    common_time = np.arange(time_ref[0], time_ref[-1], common_dt)
    f_ref = interp1d(time_ref, values_ref, kind="cubic", bounds_error=True)
    f_test = interp1d(time_test, values_test, kind="cubic", bounds_error=True)
    v_ref = f_ref(common_time)
    v_test = f_test(common_time)
    if not np.all(np.isfinite(v_ref)) or not np.all(np.isfinite(v_test)):
        raise ValueError("Interpolation produced non-finite samples")

    error = np.abs(v_ref - v_test)
    rmse = np.sqrt(np.mean((v_ref - v_test) ** 2))
    max_error = np.max(error)
    mean_error = np.mean(error)
    time_of_max = common_time[np.argmax(error)]
    pct_within = np.mean(error <= tolerance) * 100.0

    return ComparisonMetric(
        variable_name=variable_name,
        rmse=rmse,
        max_error=max_error,
        mean_error=mean_error,
        time_of_max_error=time_of_max,
        pct_within_tolerance=pct_within,
        tolerance=tolerance,
        passes=pct_within >= required_pct,
    )


def compare_powerflow(
    vm_ref: np.ndarray, va_ref: np.ndarray,
    vm_test: np.ndarray, va_test: np.ndarray,
    bus_ids: list[int] | None = None,
    tolerances: dict = DEFAULT_TOLERANCES,
) -> list[ComparisonMetric]:
    """Compare power flow results between PSSE and PowerFactory."""
    metrics = []

    # Voltage magnitude comparison
    if len(vm_ref) == len(vm_test):
        error_vm = np.abs(vm_ref - vm_test)
        tol = tolerances["powerflow_vm"]
        metrics.append(ComparisonMetric(
            variable_name="Vm_pu",
            rmse=np.sqrt(np.mean(error_vm ** 2)),
            max_error=np.max(error_vm),
            mean_error=np.mean(error_vm),
            time_of_max_error=0.0,
            pct_within_tolerance=np.mean(error_vm <= tol.value) * 100.0,
            tolerance=tol.value,
            passes=np.mean(error_vm <= tol.value) * 100.0 >= tol.percentage,
        ))

    # Voltage angle comparison
    if len(va_ref) == len(va_test):
        error_va = np.abs(va_ref - va_test)
        tol = tolerances["powerflow_va"]
        metrics.append(ComparisonMetric(
            variable_name="Va_deg",
            rmse=np.sqrt(np.mean(error_va ** 2)),
            max_error=np.max(error_va),
            mean_error=np.mean(error_va),
            time_of_max_error=0.0,
            pct_within_tolerance=np.mean(error_va <= tol.value) * 100.0,
            tolerance=tol.value,
            passes=np.mean(error_va <= tol.value) * 100.0 >= tol.percentage,
        ))

    return metrics


def compare_eigenvalues(
    eig_ref: np.ndarray,
    eig_test: np.ndarray,
    tolerances: dict = DEFAULT_TOLERANCES,
) -> list[ComparisonMetric]:
    """Compare eigenvalue sets between PSSE and PowerFactory.

    Matches eigenvalues by closest pair (greedy matching).
    """
    if eig_ref is None or eig_test is None:
        return []

    metrics = []
    tol_real = tolerances["eigenvalue_real"]
    tol_imag = tolerances["eigenvalue_imag"]

    # Greedy matching: for each test eigenvalue, find closest reference
    used = set()
    real_errors = []
    imag_errors = []

    for et in eig_test:
        best_dist = np.inf
        best_idx = -1
        for i, er in enumerate(eig_ref):
            if i in used:
                continue
            dist = abs(et - er)
            if dist < best_dist:
                best_dist = dist
                best_idx = i

        if best_idx >= 0:
            used.add(best_idx)
            real_errors.append(abs(et.real - eig_ref[best_idx].real))
            imag_errors.append(abs(et.imag - eig_ref[best_idx].imag))

    if real_errors:
        metrics.append(ComparisonMetric(
            variable_name="eigenvalue_real",
            rmse=np.sqrt(np.mean(np.array(real_errors) ** 2)),
            max_error=np.max(real_errors),
            mean_error=np.mean(real_errors),
            time_of_max_error=0.0,
            pct_within_tolerance=np.mean(np.array(real_errors) <= tol_real.value) * 100.0,
            tolerance=tol_real.value,
            passes=np.mean(np.array(real_errors) <= tol_real.value) * 100.0 >= tol_real.percentage,
        ))

    if imag_errors:
        metrics.append(ComparisonMetric(
            variable_name="eigenvalue_imag",
            rmse=np.sqrt(np.mean(np.array(imag_errors) ** 2)),
            max_error=np.max(imag_errors),
            mean_error=np.mean(imag_errors),
            time_of_max_error=0.0,
            pct_within_tolerance=np.mean(np.array(imag_errors) <= tol_imag.value) * 100.0,
            tolerance=tol_imag.value,
            passes=np.mean(np.array(imag_errors) <= tol_imag.value) * 100.0 >= tol_imag.percentage,
        ))

    return metrics
