# Strategy C: IEC CIM Intermediate Format

## Overview

Use IEC 61970 CIM (Common Information Model) as a universal intermediate format: PSSE → CIM XML → PowerFactory. This leverages the international standard for power system data exchange and provides a vendor-neutral, future-proof translation pathway.

## Rationale

IEC 61970-302 (CIM for Dynamics) specifically targets the exchange of dynamic stability models. Both PSSE (via export tools) and PowerFactory (native CIM import/export, CGMES-certified) support CIM. This is the "right" way to do model exchange per industry standards.

However, CIM dynamics support is still maturing. Not all PSSE models have CIM equivalents, and the CIM→PowerFactory mapping for dynamics is less mature than for power flow.

**This is the long-term, standards-compliant approach.** It may produce less accurate results initially but provides the strongest foundation for ongoing model exchange.

## Architecture

```
PSSE (.raw + .dyr)
    │
    ▼
PSSE → CIM Export
    │   (Options: PSS/E built-in export,
    │    ANDES → CGMES converter,
    │    or custom Python converter)
    │
    ▼
CIM XML (IEC 61970-301/302)
    │   ├── Power flow topology (CGMES)
    │   ├── Steady-state hypotheses
    │   └── Dynamic models (61970-302)
    │
    ▼
CIM Validator + Transformer
    │   ├── Schema validation (SHACL)
    │   ├── Profile compliance check
    │   └── Model-to-model transformation rules
    │
    ▼
PowerFactory CIM Import
    │   (Native, CGMES 2.4.15 / 3.0 certified)
    │
    ▼
PowerFactory Project (.pfd)
```

## Key Standards & Profiles

| Standard | Scope | Maturity |
|----------|-------|----------|
| IEC 61970-301 | CIM base (equipment model) | Mature |
| IEC 61970-302 | CIM for dynamics | Evolving |
| IEC 61970-452 | CIM XML format | Mature |
| IEC 61970-453 | CIM for network applications | Mature |
| CGMES 2.4.15 | ENTSO-E grid model exchange | Certified in PF |
| CGMES 3.0 | Latest profile | Supported in PF |

## Implementation Steps

### Step 1: PSSE → CIM Conversion
- Options for generating CIM XML from PSSE:
  1. **PSSE built-in**: PSS/E v34+ can export to CIM (limited dynamics)
  2. **ANDES + custom**: Parse via ANDES, generate CIM XML with Python
  3. **ENTSO-E CGMES converter**: Open-source tools from ENTSO-E
- Start with power flow CIM (well-supported) → verify round-trip
- Add dynamics CIM generation for standard models

### Step 2: CIM Validation
- Validate CIM XML against IEC 61970 schema
- Use SHACL shapes (PowerFactory includes a validator)
- Check profile compliance (what's missing?)

### Step 3: PowerFactory CIM Import
- Import validated CIM XML into PowerFactory
- Verify power flow results
- Check which dynamic models were imported vs. skipped
- **This is the critical gate** — if PF's CIM import doesn't handle the dynamics profile well, this strategy needs augmentation

### Step 4: CIM → DSL Gap Filler
- For dynamic models that CIM import missed:
  - Extract model definitions from CIM XML
  - Generate DSL code programmatically
  - Insert into PowerFactory project via Python API
- This is similar to Strategy B's DSL generator, but driven from CIM rather than ANDES

### Step 5: Dynamic Verification
- Same verification protocol: 3-phase fault → compare time-series
- **Key question**: Does the CIM intermediate introduce additional approximation?

### Step 6: Bidirectional Path
- Test reverse: PowerFactory → CIM → PSSE
- Verify round-trip fidelity
- Document asymmetries

## Test Harness

```python
# tests/test_strategy_c.py
"""Strategy C: CIM Intermediate Format Verification"""

import pytest
from pathlib import Path

class TestStrategyC:
    """Test CIM-based translation pipeline."""

    def test_psse_to_cim_generates(self):
        """PSSE data can be converted to CIM XML."""
        # Generate CIM XML from .raw/.dyr
        # Verify valid XML structure
        ...

    def test_cim_schema_validation(self):
        """Generated CIM XML passes schema validation."""
        # Validate against IEC 61970 XSD
        ...

    def test_cim_dynamics_profile(self):
        """Dynamic models are present in CIM output."""
        # Check for dynamics elements in 61970-302 namespace
        ...

    def test_powerfactory_cim_import(self):
        """PowerFactory successfully imports CIM XML."""
        # Import via PF API
        # Verify network topology matches
        ...

    def test_cim_powerflow_match(self):
        """Power flow via CIM path matches PSSE."""
        # Compare V, θ
        ...

    def test_cim_dynamic_models_loaded(self):
        """Dynamic models imported from CIM are functional."""
        # Check model instances exist in PF
        # Verify initialization convergence
        ...

    def test_cim_dynamic_response(self):
        """Dynamic response via CIM path matches PSSE."""
        # Same disturbance test
        ...

    def test_round_trip_fidelity(self):
        """Round-trip PSSE → CIM → PF → CIM → PSSE preserves data."""
        # Export from PF back to CIM
        # Compare with original CIM
        ...
```

## Advantages over Strategies A & B

1. **Standards-based**: Future-proof, vendor-neutral
2. **Bidirectional**: Enables PSSE ↔ PowerFactory exchange
3. **Extensible to other tools**: CIM is supported by PSS/E, PowerFactory, ETAP, eTraN, etc.
4. **Industry backing**: ENTSO-E, NERC, and EPRI all push CIM
5. **ENTSO-E operational**: CGMES is used for pan-European grid model exchange

## Limitations

1. **CIM dynamics profile is immature**: Not all PSSE models have CIM equivalents yet
2. **Two-step approximation**: PSSE → CIM → PF may lose more fidelity than direct conversion
3. **Tool dependency**: Needs CIM export from PSSE (which may need PSSE license)
4. **Documentation gap**: CIM dynamics (61970-302) specs are behind paywall (UCA membership)
5. **PowerFactory CIM dynamics import**: May not support full dynamics profile

## When to Choose This Strategy

- **Best for**: Long-term, multi-tool exchange ecosystems where standards compliance matters
- **Not ideal for**: Quick one-off translations where native import (Strategy A) suffices
- **Combine with**: Strategy B for gap-filling (CIM handles what it can, DSL generator fills the rest)

## Estimated Effort

- **Phase 1** (PSSE → CIM converter): 5-7 days
- **Phase 2** (CIM validation): 2-3 days
- **Phase 3** (PF CIM import + verification): 3-5 days
- **Phase 4** (Gap filler for dynamics): 5-10 days
- **Phase 5** (Dynamic verification): 3-5 days
- **Phase 6** (Round-trip testing): 2-3 days
- **Total**: ~3-5 weeks
