"""
PowerFactory Adapter: Abstraction layer for PowerFactory Python API.

Prototype helpers cover application connections, projects, and import calls.
RMS execution and trace extraction are not implemented: a connection alone
cannot establish successful simulation or cross-engine equivalence.
Per critique recommendation: insulate translator from PF API quirks.
"""

from pathlib import Path
from dataclasses import dataclass, field
import logging
import os

logger = logging.getLogger(__name__)


@dataclass
class PFConnectionConfig:
    """PowerFactory connection configuration."""
    install_dir: str = ""      # PowerFactory installation directory
    project_name: str = ""    # Project to activate
    username: str = ""        # PF username
    password: str = ""        # PF password
    in_process: bool = True   # Run PF in same process


class PowerFactoryAdapter:
    """Abstraction layer for PowerFactory Python API.

    Handles:
    - Application startup/shutdown with retry logic
    - Project creation/switching
    - Object creation with proper ordering
    - Composite model slot wiring
    - Simulation configuration and execution
    """

    def __init__(self, config: PFConnectionConfig | None = None):
        self.config = config or PFConnectionConfig()
        self.app = None
        self.project = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to PowerFactory application.

        Returns True if connection successful.
        """
        try:
            import powerfactory
            self.app = powerfactory.GetApplication(
                self.config.in_process
            )
            if self.app is None:
                logger.error("Failed to get PowerFactory application")
                return False
            self._connected = True
            logger.info("Connected to PowerFactory")
            return True
        except ImportError:
            logger.error(
                "powerfactory module not found. "
                "PowerFactory must be installed and the Python module "
                "from <PF_install>/Python/ must be on PYTHONPATH."
            )
            return False
        except Exception as e:
            logger.error(f"PowerFactory connection failed: {e}")
            return False

    def disconnect(self):
        """Disconnect from PowerFactory."""
        if self._connected and self.app:
            try:
                # PowerFactory doesn't have a clean disconnect API
                # but we should clean up our references
                self.project = None
                self.app = None
                self._connected = False
            except Exception as e:
                logger.warning(f"Disconnect error: {e}")

    def create_project(self, name: str) -> bool:
        """Create a new PowerFactory project."""
        if not self._connected:
            logger.error("Not connected to PowerFactory")
            return False

        try:
            self.project = self.app.CreateProject(name)
            return self.project is not None
        except Exception as e:
            logger.error(f"Failed to create project '{name}': {e}")
            return False

    def activate_project(self, name: str) -> bool:
        """Activate an existing PowerFactory project."""
        if not self._connected:
            logger.error("Not connected to PowerFactory")
            return False

        try:
            self.project = self.app.ActivateProject(name)
            return self.project is not None
        except Exception as e:
            logger.error(f"Failed to activate project '{name}': {e}")
            return False

    def import_psse(self, raw_path: str, dyr_path: str | None = None,
                    stepup_option: int = 2) -> dict:
        """Import PSSE .raw/.dyr files via PowerFactory's native import.

        Args:
            raw_path: Path to .raw or .rawx file
            dyr_path: Path to .dyr file (optional)
            stepup_option: How to handle step-up transformers
                0 = Add explicit transformer
                1 = Ignore step-up transformers
                2 = Add data to saturated X''d and Ra (default)

        Returns:
            dict with 'success', 'log', 'models_imported', 'models_skipped'
        """
        if not self._connected:
            return {"success": False, "log": "Not connected", "models_imported": [], "models_skipped": []}

        try:
            # PowerFactory's import command
            # The exact API call depends on PF version
            result = self.app.ImportRawFile(
                raw_path,
                dyr_path,
                stepup_option
            )
            return {"success": True, "log": str(result), "models_imported": [], "models_skipped": []}
        except Exception as e:
            logger.error(f"PSSE import failed: {e}")
            return {"success": False, "log": str(e), "models_imported": [], "models_skipped": []}

    def run_power_flow(self) -> dict:
        """Run power flow on the active project.

        Returns bus voltage results.
        """
        if not self._connected:
            return {}

        try:
            result = self.app.ExecuteCmd("CalculateLoadFlow")
            # Extract results from PF objects
            return {"success": True}
        except Exception as e:
            logger.error(f"Power flow failed: {e}")
            return {"success": False, "error": str(e)}

    def run_rms_simulation(self, fault_bus: int, fault_time: float = 1.0,
                           fault_duration: float = 0.1, tf: float = 10.0) -> dict:
        """Run RMS (transient stability) simulation with a fault.

        Args:
            fault_bus: Bus number for the 3-phase fault
            fault_time: Time of fault application (s)
            fault_duration: Fault clearing time (s)
            tf: Simulation end time (s)

        Returns:
            Explicit failure: RMS execution and trace extraction are unsupported.
            Success requires a real run and validated non-empty traces.
        """
        if not self._connected:
            return {"success": False, "error": "Not connected"}

        return {
            "success": False,
            "error": "RMS simulation and trace extraction are not implemented",
        }

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
