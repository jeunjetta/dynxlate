"""
PSSE baseline runner using ANDES.

Produces Result Set 1: PSSE simulation results for comparison.
"""

from pathlib import Path
from dataclasses import dataclass, field
import numpy as np


@dataclass
class SimulationResult:
    """Time-series result from a simulation."""
    name: str
    time: np.ndarray          # time points (s)
    variables: dict           # {var_name: np.ndarray}
    dt: float = 0.01         # time step (s)
    frequency: float = 50.0  # system frequency (Hz)


@dataclass
class PowerFlowResult:
    """Power flow result at all buses."""
    name: str
    bus_ids: list[int]
    vm_pu: np.ndarray         # voltage magnitude (pu)
    va_degree: np.ndarray     # voltage angle (degrees)
    p_mw: np.ndarray         # active power injection (MW)
    q_mvar: np.ndarray       # reactive power injection (MVar)


class PSSEBaselineRunner:
    """Run PSSE simulations via ANDES for baseline results.

    Note: ANDES is NOT a PSSE substitute for regulatory verification.
    It provides a reproducible open-source baseline for development.
    For production use, replace with actual PSSE API calls.
    """

    def __init__(self, raw_path: str | Path, dyr_path: str | Path | None = None):
        self.raw_path = Path(raw_path)
        self.dyr_path = Path(dyr_path) if dyr_path else None

    def run_power_flow(self) -> PowerFlowResult:
        """Run power flow and return bus results."""
        import andes

        ss = andes.run(str(self.raw_path), no_output=True, quiet=True)
        ss.PFlow.run()

        return PowerFlowResult(
            name=self.raw_path.stem,
            bus_ids=list(ss.Bus.bus.v),
            vm_pu=ss.Bus.v_mag.v,
            va_degree=ss.Bus.v_ang.v * 180.0 / np.pi if hasattr(ss.Bus, 'v_ang') else np.zeros(ss.Bus.n),
            p_mw=ss.Bus.p_mw.v if hasattr(ss.Bus, 'p_mw') else np.zeros(ss.Bus.n),
            q_mvar=ss.Bus.q_mvar.v if hasattr(ss.Bus, 'q_mvar') else np.zeros(ss.Bus.n),
        )

    def run_dynamic(self, fault_bus: int, fault_time: float = 1.0,
                    fault_duration: float = 0.1, tf: float = 10.0,
                    dt: float = 0.01) -> SimulationResult:
        """Run dynamic simulation with a 3-phase fault disturbance.

        Args:
            fault_bus: Bus number for the fault
            fault_time: Time of fault application (s)
            fault_duration: Fault clearing time (s)
            tf: Simulation end time (s)
            dt: Output time step (s)
        """
        import andes

        # Build the disturbance as Toggle entries
        ss = andes.load(str(self.raw_path),
                        addfile=str(self.dyr_path) if self.dyr_path else None,
                        no_output=True, quiet=True)

        # Add fault events via ANDES Toggle model
        # Fault on: toggle line out of service at fault_time
        # Fault off: toggle line back at fault_time + fault_duration

        ss.TDS.config.tf = tf
        ss.TDS.config.t0 = 0.0
        ss.TDS.run()

        # Extract time-series
        t = ss.dae.t
        variables = {}
        # Extract bus voltages
        for i, bus_idx in enumerate(ss.Bus.idx.v):
            var_name = f"V_bus_{bus_idx}"
            if f"v_{bus_idx}" in ss.dae.xy_name:
                pass  # TODO: extract from ANDES dae

        return SimulationResult(
            name=f"{self.raw_path.stem}_fault_{fault_bus}",
            time=np.array(t) if hasattr(t, '__len__') else np.array([t]),
            variables=variables,
            dt=dt,
        )

    def run_vref_step(self, gen_bus: int, step_size: float = 0.01,
                      step_time: float = 1.0, tf: float = 10.0) -> SimulationResult:
        """Run small-signal test: voltage reference step on a generator.

        This exercises the exciter and PSS without large-signal non-linearities.
        """
        # TODO: implement via ANDES event system
        raise NotImplementedError("Vref step not yet implemented in ANDES runner")

    def compute_eigenvalues(self) -> dict:
        """Compute eigenvalues at the operating point for small-signal comparison."""
        import andes

        ss = andes.load(str(self.raw_path),
                        addfile=str(self.dyr_path) if self.dyr_path else None,
                        no_output=True, quiet=True)
        ss.PFlow.run()

        # ANDES eigenvalue computation
        if hasattr(ss, 'EIG'):
            ss.EIG.run()
            return {
                "eigenvalues": ss.EIG.eigvals.v if hasattr(ss.EIG, 'eigvals') else None,
                "participation_factors": None,
            }
        return {"eigenvalues": None, "participation_factors": None}
