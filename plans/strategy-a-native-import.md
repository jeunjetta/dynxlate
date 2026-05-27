# Strategy A: Native PowerFactory Import + Automated Post-Processing

## Overview

Use PowerFactory's built-in PSSE `.raw`/`.dyr` import as the primary conversion path, then automate the known parameter corrections via Python + PowerFactory API.

## Rationale

PowerFactory already reads PSSE `.raw` (v27-35) and `.dyr` natively. The import handles standard library models correctly for power flow and *approximately* for dynamics. The known discrepancies (damping, saturation, load modeling, step-up transformers) are well-documented and can be systematically corrected with Python scripts.

**This is the fastest path to a working, verifiable result.**

## Architecture

```
PSSE (.raw + .dyr)
    │
    ▼
PowerFactory Native Import
    │
    ▼
Python Post-Processor (via PowerFactory API)
    ├── Fix damping constants (manual re-entry)
    ├── Fix load model exponents (CONL-activity → dynamic load)
    ├── Fix saturation parameters
    ├── Convert implicit step-up transformers to explicit
    └── Set correct voltage measurement points
    │
    ▼
PowerFactory Project (.pfd) — CORRECTED
```

## Implementation Steps

### Step 1: PSSE Baseline Simulation
- Load `.raw` + `.dyr` into PSSE (or ANDES as open-source proxy)
- Run power flow → save snapshot
- Apply 3-phase fault disturbance at a bus → run transient stability
- Export time-series: bus voltages, generator angles, line flows
- **Result Set 1**: PSSE reference results

### Step 2: PowerFactory Import
- Import `.raw` + `.dyr` via PowerFactory's built-in converter
- Note which models imported successfully vs. which were skipped
- Run power flow → compare with PSSE power flow
- **Acceptance**: V magnitude ≤0.005 pu, V angle ≤0.5° for 90%+ buses

### Step 3: Automated Post-Processing
- Write Python script using PowerFactory API (`powerfactory` module)
- Fix each known discrepancy systematically:
  1. Read damping D from `.dyr` → set corresponding PF parameter
  2. Convert loads to dynamic load model with correct exponents
  3. Apply saturation correction factors
  4. Handle step-up transformers
- Run power flow again → verify improved match

### Step 4: Dynamic Verification
- Apply same 3-phase fault in PowerFactory
- Run RMS simulation → export time-series
- Compare with Result Set 1 using normalized metrics:
  - Angle deviation: mean and max over simulation window
  - Voltage deviation: mean and max
  - Frequency deviation: mean and max
- **Acceptance**: Angle deviation ≤5°, V deviation ≤0.02 pu for 85%+ of trajectory

### Step 5: Reporting
- Generate comparison report with plots
- Document all parameter corrections applied
- Flag models that couldn't be automatically corrected

## Test Harness

```python
# tests/test_strategy_a.py
"""Strategy A: Native Import + Post-Processing Verification"""

import pytest
from pathlib import Path

MODELS_DIR = Path(__file__).parent.parent / "models"
RESULTS_DIR = Path(__file__).parent.parent / "results"

class TestStrategyA:
    """Test PSSE → PowerFactory native import + corrections."""

    def test_psse_baseline_runs(self):
        """PSSE (via ANDES) produces valid baseline results."""
        # Load .raw + .dyr in ANDES, run simulation
        # Export time-series to results/psse_baseline/
        ...

    def test_powerfactory_import_completes(self):
        """PowerFactory native import succeeds for standard models."""
        # Import .raw + .dyr via PF API
        # Verify all standard models loaded
        ...

    def test_powerflow_match(self):
        """Power flow results match within tolerance."""
        # Compare PF vs PSSE power flow
        # V ≤ 0.005 pu, θ ≤ 0.5° for 90%+ buses
        ...

    def test_damping_corrected(self):
        """Damping constants are properly set after post-processing."""
        ...

    def test_load_model_corrected(self):
        """Load models use correct voltage dependency exponents."""
        ...

    def test_dynamic_response_match(self):
        """Dynamic simulation results match within tolerance."""
        # Compare time-series:
        # Δδ ≤ 5°, ΔV ≤ 0.02 pu for 85%+ trajectory
        ...
```

## Limitations

- **Only works for standard PSSE library models** — Fortran UDMs are NOT handled
- Parameter correction is model-specific — new models need new correction rules
- Requires PowerFactory license for the import + simulation step
- The "D" parameter mismatch (load damping vs rotor friction) is a known philosophical difference — can only approximate

## Estimated Effort

- **Phase 1** (PSSE baseline + PF import): 2-3 days
- **Phase 2** (Post-processing automation): 3-5 days
- **Phase 3** (Dynamic verification + reporting): 2-3 days
- **Total**: ~2 weeks for a robust first version
