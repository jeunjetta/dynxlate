# Research: PSSE ↔ PowerFactory Dynamic Model Translation

## 1. Problem Statement

Translate transient dynamic models (generators, SVCs, inverters, etc.) from PSSE/PSCAD/SSAT formats into PowerFactory format, and verify by running the same snapshot + disturbance through both engines and comparing results.

### Source Formats
- **PSSE**: `.raw` (power flow) + `.dyr` (dynamics) — block diagram models + Fortran UDMs
- **PSCAD**: EMT models (microsecond resolution, `.psc`/`.sdb` files)
- **SSAT**: Small-signal stability models (lower than ms resolution)

### Target Format
- **PowerFactory**: `.pfd` project files, DSL (DIgSILENT Simulation Language) models, DPL scripts

---

## 2. Format Structural Comparison

### PSSE .dyr Format
- Plain text, line-based
- Each model entry: `<bus> '<model_name>' <ID> <param1> <param2> ... /`
- Model names are PSSE-specific: GENROU, GENCLS, ESST3A, EXDC2, TGOV1, IEEEG1, IEEEST, ST2CUT, etc.
- Parameters are positional — order matters, count varies per model
- Fortran UDMs compiled into `.dll`/`.so` — not portable between platforms
- Block diagrams define transfer functions (lead-lag, washout, gain blocks)

### PowerFactory DSL Format
- Object-oriented: models are instances of DSL classes stored in `.pfd` database
- DSL syntax: declarative block-diagram language with `input`, `output`, `parameter`, `block` declarations
- Composite models: combine multiple DSL models (generator + exciter + governor + PSS)
- DPL: imperative scripting for automation, NOT for model definition
- QDSL: quasi-dynamic simulation language for slower dynamics

### Key Structural Differences
| Aspect | PSSE | PowerFactory |
|--------|------|--------------|
| Generator model | Operational impedance (X''d = X''q assumed) | Coupled circuit (allows X''d ≠ X''q) |
| Damping constant | De = frequency-dependent load damping | D = rotor friction losses (NOT imported from .dyr!) |
| Saturation | Affects mutual AND leakage reactance | Affects mutual reactance only |
| Step-up transformer | Implicit in generator data | Must be explicit |
| Load modeling | CONL-activity converts for dynamics | 100% static (constant Z) by default |
| Fortran UDMs | Compiled .dll — platform specific | No direct equivalent; must re-implement in DSL |

---

## 3. Existing Tools & Approaches

### PowerFactory Native Import (BEST STARTING POINT)
- **Base package** includes PSSE import for `.raw`, `.rawx`, `.seq`, `.dyr` (versions 27-35)
- **Additional converters** (request separately): PSSE export, CIM, Integral
- **Limitation**: Only imports standard PSSE library models. Fortran UDMs (.dll) are NOT imported
- **Known issues from Karlsson (2013) thesis**:
  - Step-up transformer handling (3 options, all problematic)
  - Damping constant NOT imported
  - Saturation model differences require parameter adjustment
  - Load model defaults differ

### ANDES (Open-Source Python)
- GitHub: `curent/andes` — CURENT center, University of Tennessee
- Natively reads PSSE `.raw` v32-33 and `.dyr`
- Can convert to ANDES xlsx/json format
- Has its own simulation engine
- **Not a direct PSSE→PowerFactory bridge**, but excellent parser

### pandapower
- Has PowerFactory converter (bidirectional via DGS format)
- PSSE import capability
- **Potential intermediate format**: PSSE → pandapower → PowerFactory

### PRSIM (Manitoba Hydro / PSCAD)
- Converts PSSE `.raw`/`.dyr` and PowerFactory `.pfd` into PSCAD
- Handles dynamic data import
- **NOT bidirectional** — only goes TO PSCAD, not from PSCAD to PowerFactory
- Commercial product

### IEC CIM (61970-302 for Dynamics)
- Standard for exchanging dynamic stability models
- CIM for Dynamics (61970-302) defines generator controls, exciters, governors, PSS
- PowerFactory has CIM import/export (CGMES certified)
- **Potential universal intermediate format**
- Limitation: CIM dynamics profile is still evolving; not all PSSE models have CIM equivalents

### Dynaωo (LF Energy / RTE)
- Hybrid C++/Modelica open-source simulation suite
- Has implemented WECC generic models (REGC_A, REEC_A, REEC_B, REPC_A, WTGT_A)
- Uses Modelica as model definition language
- **Potential intermediate**: PSSE → Modelica → PowerFactory DSL

---

## 4. WECC Generic Models (Common to Both Platforms)

These models exist in standard PSSE library AND have PowerFactory equivalents:

| PSSE Model | Function | PowerFactory Equivalent |
|------------|----------|------------------------|
| REGC_A | Renewable generator/converter | ElmRco (with appropriate DSL) |
| REEC_A | Renewable electrical control (type A) | ElmDsl (REEC_A) |
| REEC_B | Renewable electrical control (type B) | ElmDsl (REEC_B) |
| REEC_C | Renewable electrical control (type C) | ElmDsl (REEC_C) |
| REPC_A | Renewable plant control | ElmDsl (REPC_A) |
| WTGT_A | Wind turbine generator type A | ElmDsl (WTGT_A) |
| WTGPT_A | Wind turbine pitch control | ElmDsl (WTGPT_A) |
| IEEEG1 | IEEE governor type 1 | ElmDsl (IEEEG1) |
| IEEEG2 | IEEE governor type 2 | ElmDsl (IEEEEG2) |
| IEEEG3 | IEEE governor type 3 | ElmDsl (IEEEEG3) |
| ESST3A | Static exciter type 3A | ElmDsl (ESST3A) |
| EXDC2 | DC exciter type 2 | ElmDsl (EXDC2) |
| IEEEST | IEEE stabilizer | ElmDsl (IEEEST) |
| ST2CUT | Stabilizer (double input) | ElmDsl (ST2CUT) |
| GENROU | Round rotor generator | ElmSym (synchronous machine) |
| GENSAL | Salient pole generator | ElmSym (synchronous machine) |
| GENCLS | Classical generator | ElmSym (simplified) |

---

## 5. Example Models Available

### Already Downloaded (in `models/psse/`)
- `kundur.raw` + `kundur_full.dyr` — 4-bus Kundur two-area system
- `ieee14.raw` + `ieee14.dyr` — IEEE 14-bus with GENROU, ESST3A, EXST1, TGOV1, IEEEG1, IEEEST, ST2CUT
- `ieee39.raw` — New England 39-bus (need .dyr from ICSEG)
- `wecc.raw` + `wecc_full.dyr` — WECC system with full dynamic models
- `wscc9.raw` — WSCC 9-bus (need .dyr)

### Available from ICSEG (Illinois)
- IEEE 14, 24, 30, 39, 57, 118, 300 bus systems
- Kundur two-area, Brazilian 7-bus, Australian 14-generator
- All in `.raw` + `.dyr` format
- URL: https://icseg.iti.illinois.edu/power-cases/

### EPRI WECC Model Guide
- URL: https://restservice.epri.com/publicdownload/000000003002027129/0/Product
- Full parameter guide for REGC_A, REEC_A/B/C, REPC_A

### WECC Approved Dynamic Model Library (Jan 2026)
- URL: https://www.wecc.org/sites/default/files/documents/progress_report/2026/Approved%20Dynamic%20Models%20January%202026.pdf

---

## 6. Feasibility Assessment

### What's EASY (standard library models)
- PSSE .raw/.dyr with standard models → PowerFactory native import handles most of this
- Power flow data: near-perfect conversion
- Standard exciters (ESST3A, EXDC2, EXST1): direct equivalents exist
- Standard governors (TGOV1, IEEEG1/2/3): direct equivalents exist
- Standard PSS (IEEEST, ST2CUT): direct equivalents exist
- WECC generic renewable models: both platforms have implementations

### What's MEDIUM (needs parameter mapping)
- Generator models: GENROU↔ElmSym requires parameter transformation (operational impedance ↔ coupled circuit)
- Saturation: different models, needs correction factors
- Damping: different definitions, needs manual adjustment
- Load models: CONL-activity ↔ dynamic load model with specific exponents
- Step-up transformers: implicit → explicit conversion needed

### What's HARD (Fortran UDMs, PSCAD, SSAT)
- Fortran UDMs (.dll): NO automated path. Must re-implement in DSL from block diagrams / source code
- PSCAD EMT models: fundamentally different simulation paradigm (EMT vs RMS). Requires model simplification/restructuring
- SSAT small-signal models: linearized representations that need to be "un-linearized" back into time-domain models
- Custom protection relay models: vendor-specific, no generic mapping

---

## 7. Key References & Links

1. Karlsson, B. "Comparison of PSSE & PowerFactory" (2013) — Uppsala University
   - https://www.diva-portal.org/smash/get/diva2:658793/FULLTEXT01.pdf
   
2. EPRI "Model User Guide for Generic Renewable Energy System Models"
   - https://restservice.epri.com/publicdownload/000000003002027129/0/Product
   - https://transmission.bpa.gov/Business/Operations/GridModeling/Model%20User%20Guide%20for%20Generic%20Renewable%20Energy%20System%20Models.pdf

3. WECC Approved Dynamic Model Library (Jan 2026)
   - https://www.wecc.org/sites/default/files/documents/progress_report/2026/Approved%20Dynamic%20Models%20January%202026.pdf

4. ANDES Documentation — PSSE RAW and DYR format
   - https://docs.andes.app/en/v1.9.3/getting_started/formats/psse.html

5. DIgSILENT PowerFactory Data Converters
   - https://www.digsilent.de/en/data-converter.html
   - https://www.digsilent.de/en/additional-data-converters.html

6. IEC 61970-302 — CIM for Dynamics
   - https://cimug.org/focus-communities/cim-for-dynamics-61970-302/

7. Dynaωo — Open-source C++/Modelica simulation
   - https://dynawo.github.io/
   - https://github.com/dynawo/dynawo

8. PRSIM — PSSE/PowerFactory → PSCAD converter
   - https://www.pscad.com/software/prsim/overview
   - https://www.pscad.com/knowledge-base/download/PRSIM-v110-Tutorial.pdf

9. ICSEG Power Cases (IEEE + custom systems in .raw/.dyr)
   - https://icseg.iti.illinois.edu/power-cases/

10. NERC Reliability Guideline: DER Modeling Parameters (2017)
    - https://www.nerc.com/globalassets/who-we-are/standing-committees/rstc/spiderwg/reliability_guideline_-_der_modeling_parameters_-_2017-08-18_-_final.pdf

11. Fraunhofer "Open-Source Industrial-Grade Collection of Renewable Energy Models"
    - https://publica.fraunhofer.de/bitstreams/b2678a04-f057-49b4-af83-af84218b29c9/download

12. CIM-Compliant Power System Dynamic Model-to-Model Transformation (IEEE)
    - https://ieeexplore.ieee.org/iel7/9424/8454923/08231176.pdf

13. PowerFactory Python API
    - https://medium.com/@Sebastian-DD/automate-powerfactory-with-python-and-powerfactory-tools-e96d33adda74
    - https://joss.theoj.org/papers/10.21105/joss.09281.pdf
