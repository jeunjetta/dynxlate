# Strategy B: ANDES-Based Parser + Modelica/DSL Code Generation

## Overview

Build a Python-based translator that parses PSSE `.raw`/`.dyr` files (using ANDES as the parser), translates each dynamic model into DSL (PowerFactory's model language), and generates a complete PowerFactory project via the Python API.

## Rationale

Strategy A depends on PowerFactory's built-in import which is a black box. Strategy B gives us **full control** over the translation of every parameter and equation. ANDES already parses `.dyr` into structured Python objects — we can map those to DSL model definitions.

This approach also handles the long-term need: **Fortran UDM translation**. If we can parse the block diagram structure (which ANDES does for standard models, and which we can extend for UDMs), we can generate equivalent DSL code.

## Architecture

```
PSSE (.raw + .dyr)
    │
    ▼
ANDES Parser → Structured Model Objects
    │
    ├── Power Flow Data → PowerFactory API (create buses, lines, loads, gens)
    │
    └── Dynamic Models → Model Registry Lookup
         ├── Standard model (GENROU, ESST3A, etc.)
         │   → Parameter mapping table → DSL instance creation
         │
         └── UDM / Unknown model
             → Block diagram extraction → DSL code generation
             (future: Fortran source → AST → DSL)
    │
    ▼
PowerFactory Project (.pfd) — FULLY CONTROLLED
```

## Key Components

### 1. PSSE Model Registry (YAML)
A comprehensive mapping from every PSSE standard model to:
- Its PowerFactory equivalent model class
- Parameter-by-parameter mapping (including unit/range corrections)
- Known discrepancies and correction factors

```yaml
# Example: registry/ESST3A.yaml
psse_model: ESST3A
pf_model: ElmDsl  # or composite model reference
pf_template: "ESST3A"  # DSL template name in PF library
parameters:
  TR:  {pf_name: TR,  scale: 1.0,  notes: "Sensor time constant" }
  VMIN: {pf_name: VMIN, scale: 1.0, notes: "Underexcitation limit" }
  VMAX: {pf_name: VMAX, scale: 1.0, notes: "Overexcitation limit" }
  KC:  {pf_name: KC,  scale: 1.0, notes: "Rectifier loading factor" }
  # ... all ESST3A parameters
corrections:
  - damping_not_imported: true
  - saturation_model_differs: true
```

### 2. DSL Code Generator
For models NOT in the registry (UDMs), generate DSL code from block diagram structure:

```python
# src/dsl_generator.py
class DSLGenerator:
    """Generate PowerFactory DSL model code from block diagram representation."""
    
    def generate(self, model_name, blocks, params):
        """Generate DSL model definition.
        
        Args:
            model_name: Name for the DSL model
            blocks: List of TransferFunction blocks from ANDES
            params: Dictionary of parameter values
        Returns:
            DSL source code string
        """
        dsl = f"model {model_name}\n"
        # Declare inputs/outputs
        # Declare parameters
        # Wire blocks together
        # Return DSL source
        return dsl
```

### 3. PowerFactory Project Builder
Uses PowerFactory Python API to programmatically create the project:

```python
# src/pf_builder.py
class PowerFactoryProjectBuilder:
    """Build a PowerFactory project from parsed PSSE data."""
    
    def __init__(self, app):
        self.app = app  # PowerFactory application object
    
    def build_from_andes(self, andes_case):
        """Create full PowerFactory project from ANDES case."""
        # Create network
        for bus in andes_case.Bus:
            self.create_bus(bus)
        for line in andes_case.Line:
            self.create_line(line)
        # ... transformers, loads, etc.
        
        # Create dynamic models
        for gen in andes_case.GENROU:
            self.create_gen_model(gen)
        for exc in andes_case.ESST3A:
            self.create_exciter_model(exc)
        # ... etc.
```

## Implementation Steps

### Step 1: ANDES Parser Integration
- Install ANDES, load example `.raw`/`.dyr` files
- Extract structured model data from ANDES objects
- Verify we can access all parameters for GENROU, ESST3A, TGOV1, IEEEST, ST2CUT
- Write extraction utilities

### Step 2: Build Model Registry
- Start with the 6-8 most common models (GENROU, GENCLS, ESST3A, EXDC2, TGOV1, IEEEG1, IEEEST, ST2CUT)
- Map each PSSE parameter to PowerFactory equivalent
- Include correction factors from Karlsson (2013) thesis
- Test with IEEE 14-bus system

### Step 3: PowerFlow Builder
- Create PowerFactory project via Python API
- Build network topology from ANDES-parsed `.raw` data
- Run power flow → verify match with PSSE
- This is the foundation for the dynamic models

### Step 4: Dynamic Model Builder
- For each model in registry: create DSL instance in PowerFactory
- Attach models to correct generators
- Set parameter values with corrections applied
- Verify model initialization (convergence of initial conditions)

### Step 5: DSL Code Generator (for UDMs)
- Define block diagram intermediate representation
- Map transfer function blocks to DSL syntax
- Generate, validate, and test with a simple custom model first

### Step 6: Dynamic Verification
- Same test as Strategy A: 3-phase fault → compare time-series
- Document any remaining discrepancies

## Test Harness

```python
# tests/test_strategy_b.py
"""Strategy B: ANDES Parser + DSL Code Generation Verification"""

import pytest
from pathlib import Path

class TestStrategyB:
    """Test parser-based translation pipeline."""

    def test_andes_parses_raw(self):
        """ANDES successfully parses .raw file."""
        from andes import andes_main
        # Load IEEE 14-bus .raw
        # Verify all buses, lines, gens extracted
        ...

    def test_andes_parses_dyr(self):
        """ANDES successfully parses .dyr file."""
        # Load IEEE 14-bus .dyr
        # Verify GENROU, ESST3A, etc. extracted with correct params
        ...

    def test_model_registry_completeness(self):
        """All PSSE models in .dyr have registry entries."""
        # Parse .dyr → get model names
        # Check each against registry YAML
        ...

    def test_parameter_mapping_accuracy(self):
        """Mapped parameters are within expected ranges."""
        # For each model, verify mapped params are physically reasonable
        ...

    def test_powerflow_via_api(self):
        """PowerFactory project built via API matches PSSE power flow."""
        # Build project, run PF, compare results
        ...

    def test_dynamic_models_initialized(self):
        """All dynamic models converge during initialization."""
        # Run initial condition calculation in PF
        ...

    def test_dynamic_response_match(self):
        """Dynamic response matches PSSE baseline."""
        # Same disturbance, same comparison metrics
        ...
```

## Advantages over Strategy A

1. **Full control**: Every parameter transformation is visible and auditable
2. **Extensible**: Adding new models = adding a YAML file
3. **UDM pathway**: DSL code generation provides a route for Fortran UDMs
4. **No black box**: We know exactly what the import did
5. **Testable**: Each component (parser, registry, builder) tested independently

## Limitations

- **Requires PowerFactory license** for the build + simulate step
- More upfront engineering than Strategy A
- DSL code generation for UDMs is the hardest part — may need iterative refinement
- PowerFactory Python API has quirks and limited documentation

## Estimated Effort

- **Phase 1** (ANDES integration + extraction): 3-5 days
- **Phase 2** (Model registry, starting 8 models): 5-7 days
- **Phase 3** (PF project builder + power flow): 3-5 days
- **Phase 4** (Dynamic model builder): 5-7 days
- **Phase 5** (DSL generator for UDMs): 5-10 days
- **Phase 6** (Verification + reporting): 3-5 days
- **Total**: ~4-6 weeks for a robust first version
