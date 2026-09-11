# EMT/IBR Context for Dynamic Model Translation

**Source:** EMT Studies Training Pack (from "EMT simulations for IBR grid" channel research)

This document captures the key EMT/IBR insights that directly impact the
dynxlate model translation project.

---

## 1. Why the EMT ↔ RMS Gap Matters for Translation

### The Core Problem
PSSE is an **RMS (phasor-domain)** simulator. PowerFactory supports **both RMS and EMT**. When translating PSSE dynamic models to PowerFactory, we have an opportunity to:

- **Option A:** Translate RMS→RMS (PSSE → PowerFactory RMS mode) — like-for-like
- **Option B:** Translate RMS→EMT (PSSE phasor → PowerFactory EMT mode) — upgrade fidelity
- **Option C:** Create both (RMS + EMT) PowerFactory models from the PSSE source

**Option B/C is where the real value lies** for IBR-rich grids like the NEM.

### Key Insight from NERC Alert Level 3 (May 2025)
> *"Real-world blackouts have occurred that RMS simulations failed to predict. EMT-DSA closes this critical gap."*

This means: if we only translate PSSE RMS models to PowerFactory RMS models, we've reproduced the same blind spot. The translation should target **PowerFactory EMT mode** for IBR models, capturing dynamics that PSSE RMS can't see.

---

## 2. IBR Models That NEED EMT Treatment

These models from our PSSE source cannot be faithfully represented in RMS:

| PSSE Model | IBR Type | EMT-Critical Behavior |
|------------|----------|----------------------|
| REGC_A/B/C | Renewable gen/converter | Current loop at kHz — RMS averages away control dynamics |
| REEC_A/B/C | Renewable elec control | PLL tracking in weak grids — RMS can't see instability |
| REPC_A | Renewable plant control | PPC interactions with nearby controllers — root cause of real oscillations |
| WTGT/WTGPT | Wind turbine | Pitch/traction control at 10-100 Hz — near RMS boundary |
| PSSPLB1 | PLB based on frequency | RoCoF detection at sub-cycle — EMT needed |
| CSVGN1 | Static var compensator | Firing angle control at kHz — RMS misses harmonics |
| Custom HVDC | VSC/LCC | PWM switching at kHz — completely invisible to RMS |

### IBR Oscillation Thresholds
- Oscillations appear at **~20% instantaneous IBR penetration** (not 60%+)
- **Dominion Energy case study:** Sustained 8 Hz post-fault voltage oscillations (3% peak) that RMS showed *nothing*
- **AEMO quote:** *"Current RMS-type models lose accuracy as the ratio of synchronous to inverter-connected generation declines"*

---

## 3. PowerFactory's Dual RMS+EMT Capability

PowerFactory is uniquely positioned because it supports **both** simulation modes:

| Mode | Time Step | What It Captures | When to Use |
|------|-----------|-----------------|-------------|
| **RMS (EMT-like)** | ~1 ms | Electromechanical transients, voltage recovery | Traditional stability studies |
| **EMT (full)** | ~10 µs | Switching, harmonics, control interactions | IBR studies, protection, weak grids |

### Translation Strategy Implication
For synchronous machine models (GENROU, GENSAL, GENCLS + exciters/governors/PSS):
- RMS translation is **sufficient** — the physics lives in the electromechanical range

For IBR models (REGC, REEC, REPC, HVDC, SVC, custom controllers):
- **EMT translation is necessary** — the physics lives inside the cycle
- PowerFactory's DSL models can be configured for both RMS and EMT simulation
- Same model structure, but EMT models need additional detail (PLL dynamics, current limits, switching)

### Action for Dynaxlate
The model registry should tag each PSSE model as:
- `sim_domain: rms` — synchronous machines, traditional controls
- `sim_domain: emt` — IBR models, HVDC, FACTS
- `sim_domain: both` — models that work in both but need different parameterization

---

## 4. Software Landscape from EMT Research

### Open-Source EMT Tools (for verification without PowerFactory license)

| Tool | Type | Use in Dynaxlate |
|------|------|-----------------|
| **DPsim** | C++/Python EMT + Phasor | Alternative EMT baseline (free, pip-installable) |
| **ParaEMT** | Python EMT (NREL) | HPC-parallel EMT, designed for IBR-rich grids |
| **ANDES** | Python RMS/transient | Already used as PSSE parser + RMS baseline |
| **pandapower** | Python steady-state | Power flow verification (already in project) |

### Commercial Tool Comparison (relevant for Ken)

| Tool | RMS | EMT | PSSE Import | Cost |
|------|-----|-----|-------------|------|
| **PowerFactory** | ✓ | ✓ | ✓ (.raw/.dyr native) | ~$15-40k/yr |
| **PSCAD/EMTDC** | ✗ | ✓ | Via PRSIM | ~$10-30k/yr |
| **EMTP-RV** | ✗ | ✓ | Partial | ~$8-25k/yr |
| **OPAL-RT** | ✗ | ✓ (real-time) | ✓ (IEEE 118 import) | HIL hardware cost |

### Key Takeaway
**PowerFactory is the best target** for the translation because:
1. It's the only tool that does both RMS and EMT natively
2. It already has PSSE import (our Strategy A)
3. IBR models translated to EMT in PowerFactory can be simulated in RMS mode too (for comparison)
4. No other single tool gives us this flexibility

---

## 5. IBR-Specific Verification Protocol

### Beyond the Standard 3-Phase Fault
The critique recommended multiple disturbances. For IBR models, add:

| Disturbance | What It Tests | PSSE Can Do? | PF EMT Can Do? |
|-------------|--------------|--------------|-----------------|
| 3-phase fault (5-6 cycle) | Large-signal stability | ✓ | ✓ |
| Vref step (1%) | Exciter/PSS linearity | ✓ | ✓ |
| Generator trip | Governor/freq response | ✓ | ✓ |
| **Weak grid (low SCR)** | PLL stability | ✗ | ✓ |
| **Voltage dip (0.5 pu, 100ms)** | IBR ride-through | Partial | ✓ |
| **Frequency ramp** | FFR/synthetic inertia | ✗ | ✓ |
| **Control interaction** | Multi-PPC oscillation | ✗ | ✓ |

### SCR Sensitivity Testing
For IBR models, run the translated PowerFactory EMT model at multiple SCR values:
- SCR = 10 (strong grid) — should match PSSE RMS
- SCR = 5 (moderate) — starting to diverge
- SCR = 3 (weak) — RMS-EMT gap becomes significant
- SCR = 1.5 (very weak) — RMS completely invalid

This is the **smoking gun test** — if the translated EMT model matches PSSE at SCR=10 but shows different (more correct) behavior at SCR=3, the translation is working.

---

## 6. Dominion Energy Lessons for AEMO

From the case study (Dominion Energy, Virginia/North Carolina):

1. **PPC interactions are the #1 oscillation cause** — controllers tuned independently without considering nearby controllers. AEMO's NEM has the same problem with many IBR plants in close proximity.

2. **SCADA completely misses IBR oscillations** — WAMS/PMU data is essential for model validation.

3. **Switching voltage → power factor control** is the #1 quick fix for oscillations. The translated PowerFactory model should be able to demonstrate this.

4. **Oscillations appear at sunrise/sunset** (low IBR output periods). NEM's duck curve makes morning/evening ramps highest-risk.

5. **One oscillation event can involve 6+ controllers** — system-wide model fidelity matters.

---

## 7. Regulatory Drivers for EMT Translation

| Standard | Requirement | Impact on Dynaxlate |
|----------|-------------|---------------------|
| **IEEE 2800-2022** | EMT-level verification for IBR transmission connection | Translated IBR models must work in PF EMT mode |
| **IEEE 1547-2018** | DER ride-through verification | DER models need EMT translation |
| **NERC Alert L3 (May 2025)** | Generator Owners report EMT modeling processes | AEMO needs documented EMT workflow |
| **AEMO Grid Code** | Increasing EMT study requirements for NEM connections | Direct business case for this tool |

---

## 8. Updated Strategy Recommendations

### New Strategy A+: Native Import + EMT Upgrade
After Strategy A (native RMS import + corrections), add:
- **Step 6:** For IBR models, switch PowerFactory simulation mode from RMS to EMT
- **Step 7:** Run EMT simulation at multiple SCR values
- **Step 8:** Compare EMT results against PMU field data (if available from AEMO WAMS)

### New Verification: SCR Sensitivity Matrix
Add to all strategies:
- Run translated model at SCR = {10, 5, 3, 1.5}
- At SCR=10: should match PSSE RMS (baseline equivalence)
- At SCR≤3: should show EMT-specific phenomena (PLL instability, oscillations) that PSSE can't reproduce
- This validates the translation AND demonstrates the value of EMT mode

### New Test Case: IBR-Dominant System
The WECC test case (`wecc.raw` + `wecc_full.dyr`) in our models/ directory
is ideal because it contains IBR models (REGC, REEC, REPC).

---

## References from EMT Training Pack

- ESIG — "EMT Simulation Models for Large-Scale System Impact Studies" (Badrzadeh, 2019)
- OPAL-RT — "RMS vs EMT Simulation for IBRs Explained" (2025)
- NERC Alert Level 3 — EMT Modeling Processes (May 2025)
- Dominion Energy — Case Study: Oscillation Detection & PPC Interactions (2024)
- EMTP — EMT-DSA Product Overview (2025)
- NREL — ParaEMT: Open-Source Parallel EMT Simulator (Xiong et al., 2024)
- IEEE 2800-2022, IEEE 1547-2018
- PAC World / SEL — "IBR Oscillations and Grid Reliability" (Purcell, Wold et al., 2024)
