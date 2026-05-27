# Critique: PSSE-to-PowerFactory Dynamic Model Translation Strategies

**Reviewer**: Senior Power Systems Engineer (20+ years PSSE, PowerFactory, PSCAD, WECC/NERC model validation)  
**Date**: 2026-05-28  
**Scope**: Critical review of Strategy A (Native Import), Strategy B (ANDES+DSL), Strategy C (CIM Intermediate)

---

## 1. What Each Strategy Gets RIGHT

### Strategy A: Native Import + Post-Processing

**Correctly identifies the fastest path to value.** PowerFactory's built-in PSSE import is genuinely the shortest distance between a `.dyr` file and a working simulation. For standard library models, this is a solved problem — DIgSILENT has been refining this converter for 15+ years. Starting here avoids NIH (Not Invented Here) syndrome.

**Honest about the D parameter philosophical difference.** The plan correctly notes that PSSE's "D" (load-frequency damping, essentially a system-wide parameter) and PowerFactory's "D" (rotor mechanical friction) are fundamentally different quantities. This isn't a bug — it's a design philosophy divergence. Acknowledging this upfront saves weeks of chasing phantom discrepancies.

**Practical verification thresholds.** The acceptance criteria (V ≤ 0.005 pu, θ ≤ 0.5° for PF; Δδ ≤ 5°, ΔV ≤ 0.02 pu for dynamics) are reasonable starting points that align with industry practice for cross-platform model comparison.

**Right-sizing the effort estimate.** ~2 weeks is realistic for someone who knows both tools. This isn't research — it's engineering execution.

### Strategy B: ANDES Parser + DSL Code Generation

**Correctly identifies that full control is needed for auditability.** In a regulatory environment (AEMO, NERC, ENTSO-E), you need to explain *exactly* what transformation was applied to every parameter. PowerFactory's native import is a black box — you get a result but can't produce a traceable parameter-by-parameter transformation report. Strategy B solves this.

**YAML-based model registry is the right design.** A declarative mapping file per model (rather than hardcoded Python) is maintainable, reviewable, and diff-able. This is how GridCal, pandapower, and ANDES itself handle format mappings. It also enables non-programmers (power engineers) to contribute corrections.

**Identifies the UDM pathway as the long-term differentiator.** Strategy A fundamentally cannot handle Fortran UDMs. Strategy B at least provides an architectural pathway, even if the implementation is deferred.

**Component-level testing is well thought out.** The test harness tests parser, registry, builder, and simulator independently. This is good software engineering.

### Strategy C: CIM Intermediate Format

**Correctly identifies the long-term strategic direction.** CIM/CGMES is where the industry is heading. ENTSO-E mandates CGMES for all TSO data exchange in Europe. NERC is pushing CIM adoption in North America. AEMO's own market modelling will inevitably encounter CIM requirements. Building CIM competency now has strategic value beyond this project.

**Identifies the bidirectional use case.** If KaR ever needs to go PowerFactory → PSSE (which happens when sharing models with NEM participants who use PSSE), having a CIM pipeline is the only clean path. Strategies A and B are one-directional.

**Acknowledges CIM dynamics immaturity honestly.** The plan doesn't oversell CIM — it correctly flags that 61970-302 (CIM for Dynamics) is still evolving and that many PSSE models lack CIM equivalents. This intellectual honesty is important.

---

## 2. What Each Strategy Gets WRONG or Is MISSING

### Strategy A — Critical Gaps

**1. Underestimates the post-processing complexity.** The plan lists five corrections (damping, load model, saturation, step-up transformer, voltage measurement) as if they're equally tractable. They're not:

- **Saturation correction** is not a simple parameter substitution. PSSE saturation affects *both* mutual and leakage reactance via Se(Xd) and Se(Xq) curves; PowerFactory saturation only affects mutual reactance. The correction requires converting Se values to PowerFactory's `Sats`/`Sato` format using iterative calculation. Karlsson (2013) documents this but the plan doesn't specify the algorithm.
- **Step-up transformer handling** has *three options* in PowerFactory import, and the "right" choice depends on whether the generator was modelled with embedded transformer in PSSE (common in NEM) or without. The plan doesn't specify a decision procedure.
- **Load model conversion** requires knowing the CONL activity percentages from the PSSE case — information that isn't in the `.dyr` file and may not even be in the `.raw` file. It's often set separately in PSSE's dynamic activity setup.

**2. No error taxonomy from the import.** When PowerFactory imports a `.dyr`, it produces an import log listing which models were imported, which were skipped, and which had warnings. The plan doesn't specify how to systematically parse this log, categorise the failures, and route them to the correct post-processor. This is the *first* thing you need — without it, you don't know what to fix.

**3. "ANDES as PSSE proxy" is problematic.** Step 1 says "Load `.raw` + `.dyr` into PSSE (or ANDES as open-source proxy)." ANDES is *not* a PSSE substitute for verification. ANDES uses its own numerical integration, its own solver, and its own model implementations. The results will differ from PSSE — sometimes significantly for stiff systems. If you're comparing PowerFactory results to ANDES rather than PSSE, you're validating against the wrong reference. This should use PSSE itself (AEMO has licenses) or accept the discrepancy explicitly.

**4. No handling of model interconnection topology.** The plan focuses on parameter corrections but doesn't address how PSSE's convention for connecting exciters, governors, and PSS to generators (via bus number + machine ID) maps to PowerFactory's composite model slot architecture. PowerFactory uses a "frame" concept where dynamic models are connected through named slots. This mapping is non-trivial and a frequent source of silent errors (models that "initialize" but aren't actually connected).

**5. No mention of .rawx format.** PSSE v34+ uses `.rawx` (XML-based) as the primary format. The `.raw` format is legacy. PowerFactory's import handles both, but the plan should specify which is being used for testing and whether `.rawx` provides better data fidelity.

### Strategy B — Critical Gaps

**1. Vastly underestimates the model registry effort.** Starting with "6-8 most common models" and spending "5-7 days" on the registry is wildly optimistic. Each PSSE model has dozens of parameters, and each parameter needs:
- PSSE parameter name, position, type, range, default
- PowerFactory parameter name (which differs from PSSE names)
- Unit conversion (PSSE uses mixed units; PowerFactory has its own conventions)
- Scaling factor
- Conditional logic (some parameters only apply when others have certain values)
- Cross-platform validation data

For ESST3A alone there are 22 parameters. For IEEEG1 there are 21. Doing 8 models *properly* with validation is 3-4 weeks of careful engineering, not 5-7 days.

**2. DSL code generator is underspecified.** The `DSLGenerator` class shows `model {model_name}` as the DSL syntax — but that's not valid DSL. DSL models in PowerFactory are defined using `class` declarations with `input`, `output`, `parameter`, and block definitions using a specific syntax:

```
class ESST3A {
  input Vt, Vref, Ifd;
  output Efd;
  parameter TR, VMIN, VMAX, KC, ...
  block ... 
}
```

The plan should show actual DSL syntax examples to prove the generator architecture is feasible.

**3. ANDES doesn't parse UDM block diagrams.** The plan says "Block diagram extraction → DSL code generation" for UDMs, but ANDES's `.dyr` parser only handles standard PSSE library models. When it encounters a UDM name, it either skips it or raises an error. ANDES has *no* infrastructure for parsing Fortran source code or block diagram definitions. The "(future: Fortran source → AST → DSL)" note is essentially a whole PhD thesis. The plan needs to be honest that UDM support is aspirational, not architectural.

**4. PowerFactory Python API documentation gap.** The plan says "PowerFactory Python API has quirks and limited documentation" — this is a severe understatement. The API:
- Requires PowerFactory to be running (it's a COM Automation interface on Windows, or a custom RPC on Linux)
- Has inconsistent object naming (some are `ElmXxx`, others are `RelXxx`, `StaXxx`)
- Documentation is spread across DIgSILENT's help system, not consolidated
- Object creation order matters (you can't attach a dynamic model to a generator that doesn't exist yet)
- Error messages are often just "method failed" with no detail
- The Python module (`powerfactory.py`) shipped with PowerFactory is a thin wrapper that needs the PF application object

This needs a dedicated "API Compatibility Layer" to insulate the translator from PF API quirks.

**5. No incremental verification strategy.** The plan goes straight from "build everything" to "compare dynamic results." A better approach would be:
- Build power flow only → verify PF match
- Add one model type (e.g., GENROU) → verify initial conditions
- Add exciter → verify small-signal response (eigenvalues)
- Add governor → verify frequency response
- Add PSS → verify damping improvement

This incremental approach catches interconnection errors early.

### Strategy C — Critical Gaps

**1. No working PSSE → CIM dynamics converter exists.** The plan lists three options for PSSE → CIM, but none of them actually work for dynamics today:
- PSSE built-in CIM export (v34+): Only exports power flow (61970-301), not dynamics (61970-302). Siemens/PTI has talked about dynamics CIM export for years but it's not in the released product.
- ANDES → CGMES: ANDES can export to its own JSON/xlsx format. There's no CGMES/CIM export from ANDES. The `andes.interop.pypowsybl` module exists but is experimental and doesn't handle dynamics.
- ENTSO-E CGMES converter: These tools convert *between* CIM profiles, not from PSSE to CIM. They assume you already have CIM XML.
- **Custom Python converter**: This is the actual option, and it's essentially "build Strategy B, then add CIM serialization." The effort is Strategy B + additional CIM schema work.

The plan needs to be honest that the PSSE → CIM step is largely unwritten software.

**2. PowerFactory CIM dynamics import is untested territory.** PowerFactory is CGMES-certified for *power flow* (61970-301/452/453). The dynamics profile (61970-302) is a different matter. DIgSILENT's documentation on CIM dynamics import is sparse, and I've not seen independent validation of PowerFactory importing CIM 61970-302 data and producing correct dynamic simulations. This is a critical gate that could kill the strategy — it must be tested *first*, not assumed.

**3. Round-trip fidelity testing is premature.** Step 6 proposes PSSE → CIM → PF → CIM → PSSE round-trip testing. This is a noble goal but the forward path isn't even working yet. The effort estimate includes 2-3 days for round-trip testing, which is unrealistic even if the forward path works. Round-trip testing requires solving the inverse mapping for every parameter transformation — essentially building Strategy B in reverse.

**4. Missing the "CIM profile" complexity.** CIM isn't one thing — it's a family of profiles. CGMES 2.4.15 and CGMES 3.0 have different schemas. The dynamics profile adds another layer. Which profile combination does PowerFactory actually import? The plan needs to specify exact profile versions and test against them.

**5. SHACL validation is necessary but insufficient.** Validating CIM XML against SHACL shapes checks structural conformance (all required fields present, types correct) but doesn't check *semantic* validity (parameter values in reasonable ranges, model interconnections correct). You need both.

---

## 3. Critical Gaps or Risks NOT Addressed by Any Strategy

### 3.1 Numerical Equivalence vs. Physical Equivalence

None of the strategies distinguish between *numerical equivalence* (same numbers out of both simulators for the same input) and *physical equivalence* (same physical behaviour, possibly with different numerical values due to different model formulations). For example:

- GENROU in PSSE assumes X''d = X''q (round rotor approximation). PowerFactory's ElmSym allows X''d ≠ X''q. If you set X''d = X''q in PowerFactory, you get numerical equivalence. If you use actual X''d ≠ X''q values from generator test reports, you get better physical fidelity but different numbers. **Which does AEMO want?** This needs a policy decision.

### 3.2 Initial Condition Convergence

None of the strategies address the problem that dynamic models may not converge during PowerFactory's initial condition calculation. PSSE's approach to initial conditions (solving the algebraic part of the differential-algebraic system at t=0) differs from PowerFactory's approach (a separate initialisation pass using a different solver). Models that initialise in PSSE can fail to initialise in PowerFactory — especially with aggressive controller limits or saturation. The strategies need an "initial condition debugging" phase.

### 3.3 Solver and Integration Method Differences

PSSE uses a fixed-step trapezoidal rule (typically 0.5-2 cycle step). PowerFactory defaults to a variable-step DAE solver. Different solvers produce different results for the same model — this is a *solver effect*, not a *model effect*. The verification methodology doesn't isolate the two. Recommendation: run PowerFactory with a fixed-step solver matching PSSE's step size for the comparison, then separately test with the variable-step solver.

### 3.4 Network Frequency Model

PSSE and PowerFactory model system frequency differently. PSSE uses a "system reference frequency" derived from the centre-of-inertia. PowerFactory computes frequency at each bus from the voltage phase angle derivative. For large systems, these produce different frequency profiles during disturbances. This is a known source of discrepancy not addressed in any strategy.

### 3.5 Relay and Protection Models

The research document mentions "custom protection relay models" as HARD, but no strategy addresses them. In AEMO's NEM models, protection relays (distance relays, under-frequency load shedding, special protection schemes) are critical for determining post-contingency trajectories. These are often implemented as UDMs in PSSE. Ignoring them means the translated model can't reproduce the same cascading behaviour.

### 3.6 HVDC and FACTS Models

None of the strategies address HVDC (VSC, LCC) or FACTS (SVC, STATCOM, TCSC) models. The NEM has several HVDC links (Basslink, Murraylink, etc.) and numerous SVCs. These have dedicated PSSE models (CSVGN1, SVC, PSSPLB1) that require specific translation. The research document's WECC model table doesn't cover these.

### 3.7 Renewable Energy Model Versioning

WECC renewable models are actively being revised. REGC_A → REGC_B, REEC_A → REEC_B → REEC_C, REPC_A → REPC_B. PowerFactory's built-in models may be at a different revision than PSSE's. The plans need a model version compatibility matrix.

### 3.8 License and Deployment Constraints

All three strategies require a PowerFactory license for the final build/simulate step. But Strategy B also requires PowerFactory to be *running* during project construction (the Python API is a live connection, not a file generator). This means:
- You can't build projects in a CI/CD pipeline without a PowerFactory license server
- You can't parallelise project building across multiple workers without multiple licenses
- You need to handle PF application startup/shutdown in scripts (it's flaky)

Strategy A also has this problem (post-processing via API). Only the DSL *generation* part of Strategy B could theoretically work offline — if you generate DSL files and import them via PowerFactory's file import rather than the Python API.

---

## 4. Recommendations for Improvement

### Strategy A Improvements

1. **Add an import log parser.** Before any post-processing, systematically parse the PowerFactory import log to classify: (a) models imported correctly, (b) models imported with warnings, (c) models skipped. Route each category to the appropriate handler.

2. **Specify the saturation correction algorithm.** Implement the Sauer/Pai or Karlsson conversion procedure for Se(1.0)/Se(1.2) → PowerFactory's Sata/Satb format. This is well-documented; just do it.

3. **Replace ANDES as baseline with actual PSSE.** AEMO has PSSE licenses. Use them. If PSSE isn't available for a specific test, use ANDES but explicitly document the expected ANDES-vs-PSSE discrepancies.

4. **Add composite model connection verification.** After import, write a script that verifies every dynamic model is actually connected to its generator (check the composite model slots, not just that the object exists).

5. **Add a `.rawx` test path.** Test with both `.raw` and `.rawx` to determine which provides better import fidelity.

6. **Document the step-up transformer decision procedure.** If the PSSE generator data includes Xsource (embedded transformer impedance), use Option 3 (explicit transformer). If not, use Option 1 (embedded in generator). This should be automatic.

### Strategy B Improvements

1. **Scope the model registry to Phase 1 models only, but do them rigorously.** Start with exactly the models in the test files: GENROU, ESST3A, EXDC2, TGOV1, IEEEG1, IEEEST, ST2CUT, EXST1, ESDC2A. That's 9 models. Do each one with full parameter mapping, unit conversion, range validation, and at least two test cases. Budget 3 weeks minimum.

2. **Define the DSL syntax properly.** Before writing the generator, hand-translate one model (ESST3A is a good candidate) from PSSE to DSL and validate it in PowerFactory. This proves the DSL mapping is correct before automating it.

3. **Add a PowerFactory API abstraction layer.** Create a `PowerFactoryAdapter` class that wraps the PF Python API with consistent error handling, retry logic, and connection management. This should handle:
   - Application startup/shutdown
   - Project creation/switching
   - Object creation with proper ordering
   - Composite model slot wiring
   - Simulation configuration and execution

4. **Implement incremental verification.** Build and verify in layers: network → generators → exciters → governors → PSS. Run power flow and initial condition checks at each layer.

5. **Be honest about UDM timeline.** Separate the UDM pathway into a distinct Phase 2 with its own effort estimate (4-8 weeks, not the 5-10 days listed). The current estimate is off by 4-8x.

6. **Add eigenvalue comparison.** Before running time-domain simulations, compare eigenvalues between PSSE and PowerFactory at the operating point. This is a far more sensitive test than time-domain comparison and catches parameter errors immediately. ANDES can compute eigenvalues for the PSSE side.

### Strategy C Improvements

1. **Validate the CIM dynamics import gate FIRST.** Before building any converter, test PowerFactory's ability to import CIM 61970-302 data. Create a minimal CIM XML with one generator + one exciter, import it, and verify the dynamic model is functional. If this fails, Strategy C is dead on arrival for dynamics (but may still be valuable for power flow).

2. **Build on Strategy B, don't duplicate it.** The PSSE → CIM converter needs the same parser (ANDES) and the same model registry (parameter mappings) as Strategy B. The only addition is a CIM serializer. Architect the code so Strategy B's registry and parser are reused, with CIM export as an output format option alongside DSL.

3. **Use pypowsybl for CIM validation.** pypowsybl (the Python wrapper for PowSyBl, an open-source CGMES toolchain) can validate CIM/CGMES files and even perform power flow. Use it as an independent CIM validator before PowerFactory import.

4. **Drop round-trip testing from initial scope.** Focus on one-directional PSSE → CIM → PF. Round-trip is a separate project.

5. **Specify exact CIM profile versions.** Target CGMES 3.0 (latest, PowerFactory supports it) with the Dynamics profile at the highest available maturity level. Document which specific classes and associations are needed for each PSSE model.

6. **Budget honestly.** Strategy C is not "3-5 weeks." It's "Strategy B effort (4-6 weeks) + CIM serialization work (2-3 weeks) + CIM validation infrastructure (1-2 weeks) + PowerFactory CIM import debugging (unknown, possibly 2-4 weeks)." Realistic total: 8-15 weeks.

---

## 5. Which Strategy to START With and Why

**Start with Strategy A. Then build Strategy B on top of it.**

Rationale:

1. **Strategy A produces results in 2 weeks.** You can import IEEE 14-bus, apply corrections, and compare dynamic responses within a sprint. This gives you:
   - A working PowerFactory model to study
   - A quantified baseline of how good the native import is
   - A list of *specific* failures (not theoretical ones)
   - Confidence that the approach is viable

2. **Strategy A reveals the actual correction workload.** You don't know which corrections matter until you measure. Maybe the saturation correction only changes angle by 0.2° and isn't worth automating. Maybe the damping correction changes frequency by 0.5 Hz and is critical. Strategy A gives you the data to prioritise Strategy B's registry work.

3. **Strategy A's post-processing IS Strategy B's registry, just smaller.** The Python scripts you write for Strategy A corrections are the seed code for Strategy B's model registry. Every correction function you write becomes a parameter mapping rule.

4. **Strategy A is the best way to learn the PowerFactory API.** You'll discover the API quirks, the composite model connection issues, and the initial condition problems in a low-stakes context (fixing import results) before trying to build from scratch (Strategy B).

5. **Strategy A sets the verification methodology.** The comparison framework (time-series export, metric calculation, tolerance checking) you build for Strategy A is *exactly* what you need for Strategies B and C.

**Do NOT start with Strategy C.** It has the highest risk of "spend 3 weeks building a CIM pipeline that doesn't work for dynamics" with no intermediate deliverable. Strategy C is a *Phase 3* activity, not a starting point.

**Sequence**: A (2 weeks) → B (4-6 weeks) → C (build on B, 4-8 weeks additional)

---

## 6. How the Strategies Could Be COMBINED for Best Results

### The "Layered Translation" Architecture

```
PSSE (.raw + .dyr)
    │
    ├── Layer 1: Native Import (Strategy A)
    │   └── Get 80% of the way there automatically
    │   └── Produces: PF project + import log
    │
    ├── Layer 2: Post-Processor / Corrector (Strategy A + B hybrid)
    │   └── Reads import log → identifies failures
    │   └── For known corrections: applies from model registry (Strategy B)
    │   └── For failed imports: uses ANDES parser + DSL generator (Strategy B)
    │   └── Produces: Corrected PF project
    │
    ├── Layer 3: Verification Framework (shared across all)
    │   └── Eigenvalue comparison at operating point
    │   └── Time-domain comparison for specified disturbances
    │   └── Parameter-by-parameter diff report
    │
    └── Layer 4: CIM Export (Strategy C, built on Layer 2's registry)
        └── Uses the same model registry to serialize to CIM
        └── Enables PSSE ↔ PF bidirectional exchange
        └── Enables exchange with other CIM-capable tools
```

**Key insight**: Strategy A is the import *engine*, Strategy B is the *correction/extension* framework, Strategy C is the *export* pathway. They're not alternatives — they're layers.

The model registry from Strategy B serves ALL layers:
- Layer 1: Documents what the native import does (for audit)
- Layer 2: Provides correction rules and DSL generation for gaps
- Layer 3: Defines expected parameter values for verification
- Layer 4: Provides parameter mappings for CIM serialization

---

## 7. Specific Concerns About the Fortran UDM Path

### The UDM Problem is Harder Than Any Strategy Acknowledges

**7.1 No automated Fortran parsing exists.** ANDES cannot parse Fortran UDMs. PSSE doesn't expose the block diagram structure of UDMs through any API or file format — the `.dyr` file just has a model name and parameters. The actual model logic lives in:
- The compiled `.dll`/`.so` (binary, not decompilable)
- The original Fortran source (may not be available, especially for vendor models)
- The PSSE block diagram graphical representation (only accessible through PSSE GUI)

**7.2 The source code availability problem.** For AEMO's NEM models, Fortran UDMs come from several sources:
- **In-house developed**: Source code available (good)
- **OEM-provided** (ABB, Siemens, GE): Source code may be under NDA or simply not provided (bad)
- **Consultant-developed**: Source code availability depends on the contract (variable)
- **Legacy**: Original author may have left, source lost (worst case)

Without source code, the only option is to reverse-engineer the UDM from its *behaviour* (black-box testing with systematic inputs) — which is expensive, approximate, and legally questionable for vendor models.

**7.3 The DSL equivalence problem.** Even with Fortran source, translating to DSL is not straightforward:
- Fortran allows arbitrary computation (loops, conditionals, arrays, file I/O)
- DSL is a block-diagram language — it only supports transfer functions, summation, gain, limits, and lead-lag blocks
- Fortran UDMs often include look-up tables, IF-THEN-ELSE logic, and state machines that have no direct DSL equivalent
- PowerFactory's QDSL (Quasi-Dynamic Simulation Language) is closer to procedural code but has different semantics and is less well-supported

**7.4 Practical recommendation for UDMs:**

**Tier 1** (Standard model equivalents): Check if the UDM is actually a standard model with minor modifications. Many "UDMs" in NEM are just IEEEG1 or ESST3A with non-standard parameter values. These can be handled by Strategy B's registry.

**Tier 2** (Source code available): Build a Fortran → DSL translator for the subset of Fortran that maps to block diagrams (gains, lead-lag, washout, limits). This handles ~70% of typical UDMs. Remaining logic (look-up tables, state machines) must be hand-translated.

**Tier 3** (No source code, behaviour only): Run the UDM in PSSE with systematic test signals (step inputs, frequency ramps, voltage dips) and use the response data to fit a simplified DSL model. This is model identification, not translation — it's approximate by nature.

**Tier 4** (Complex models — HVDC, protection, special schemes): Accept that these require manual re-implementation in DSL by a domain expert. Budget 2-5 days per model.

**7.5 ANDES UDM parsing is not happening.** The plan mentions "Block diagram extraction" from ANDES for UDMs. ANDES does not and will not parse UDM block diagrams — this is outside its scope. ANDES's developer (Hantao Cui) has explicitly stated that UDM support is not on the roadmap. Remove this from the architecture.

---

## 8. Specific Concerns About PSCAD/SSAT Translation

### PSCAD (EMTDC) Translation

**8.1 Fundamental paradigm mismatch.** PSCAD is an electromagnetic transient (EMT) simulator with microsecond time steps. PowerFactory's RMS simulation is a fundamentally different simulation paradigm. Translation requires:

- **EMT → RMS simplification**: PSCAD models include high-frequency dynamics (sub-synchronous resonance, DC-link ripple, switching transients) that have no RMS equivalent. These must be removed.
- **Phasor approximation**: PSCAD's time-domain differential equations must be converted to phasor-domain algebraic + differential equations. This is well-understood for standard models but non-trivial for custom EMT models.
- **Controller equivalence**: PSCAD controller models use instantaneous values (abc frame or dq frame with no frequency assumption). RMS controllers use phasor quantities. The translation depends on the assumed system frequency and may not preserve all controller dynamics.

**8.2 PRSIM only goes one direction.** The research document mentions PRSIM (PSSE/PF → PSCAD), but KaR needs the reverse (PSCAD → PF). PRSIM can't help here.

**8.3 Practical approach for PSCAD:**

- Don't try to translate PSCAD models directly. Instead, identify the *physical device* (e.g., "this is a VSC-HVDC converter") and implement the corresponding RMS model in PowerFactory using standard WECC/NEM generic models.
- Use PSCAD simulation results as validation data (run the same disturbance in both PSCAD and the translated PF model).
- For custom PSCAD models with no RMS equivalent, the re-implementation effort is essentially the same as UDM Tier 4 — 2-5 days per model with domain expertise.

### SSAT (Small-Signal) Translation

**8.4 "Un-linearizing" is not a thing.** SSAT provides linearized state-space models (A, B, C, D matrices) at a specific operating point. You can't "un-linearize" these back into a time-domain model because the linearization destroys information about limits, saturation, and non-linear control actions.

**8.5 What SSAT models ARE good for:** Eigenvalue comparison. If you've translated a PSSE model to PowerFactory (via Strategy A or B), you can compute eigenvalues in PowerFactory at the same operating point and compare them to SSAT's results. This is actually the *best* validation test — far more sensitive than time-domain comparison.

**8.6 Practical approach for SSAT:**

- Treat SSAT as a **validation tool**, not a translation source.
- After translating PSSE → PF, compute eigenvalues in PowerFactory and compare with SSAT eigenvalues. Mismatches immediately reveal parameter or structural differences.
- For the specific case where you only have SSAT models (no PSSE source): You can reconstruct a simplified time-domain model by identifying the transfer function structure from the state-space matrices, but this requires knowing what physical device the model represents. It's essentially system identification from linearized data — useful but approximate.

---

## 9. Australian-Specific Considerations (AEMO, NEM)

### 9.1 NEM Dynamic Model Library

AEMO maintains a NEM Dynamic Model Library with specific generator, exciter, governor, and PSS models for every generating unit in the NEM. These are provided as PSSE `.dyr` entries. Key considerations:

- **AEMO's model naming convention** may differ from WECC/IEEE. NEM models often use OEM-specific names (e.g., "ABB Unitrol" rather than "ESST3A"). You need a mapping from NEM naming to PSSE standard naming.
- **AEMO's model data quality process** (OPDMS — Operational Data Management System) means parameters have already been validated against PSSE. This is good — you're starting with clean data.
- **AEMO may have custom UDMs** for specific generators (especially hydro plants in Tasmania/Snowy, and the newer wind/solar farms). These are the Tier 2-4 UDM problem.

### 9.2 NEM Frequency Operating Standards

Australia's frequency operating standards (FOS) define different frequency bands than WECC/NERC. PowerFactory's default under-frequency load shedding and generator protection settings are configured for European/NERC standards. After translation, you MUST configure:
- Under-frequency load shedding (UFLS) scheme per NEM requirements
- Generator frequency relay settings per NEM standards
- Over-frequency generator tripping per NEM requirements
- Special Protection Schemes (SPS) specific to NEM regions

These are often implemented as UDMs in PSSE, making them a Tier 3-4 UDM translation problem.

### 9.3 AEMO's SSAT Usage

AEMO uses SSAT extensively for small-signal stability analysis of the NEM. If the translated PowerFactory models are to be validated against AEMO's SSAT results, you need eigenvalue comparison capability (Recommendation 4.2 above). This is a specific verification requirement.

### 9.4 Australian Solar and Wind Models

Australia has a high penetration of inverter-based resources (IBR). AEMO requires specific IBR models that may differ from WECC generic models:
- **AEMO's Generating System Model Guidelines** (latest revision) specify model requirements
- Some Australian IBR models are based on WECC REGC_A/REEC_B/REPC_A but with NEM-specific parameter tuning
- AEMO has been developing its own generic IBR models (AEMO-GEN, AEMO-GRID) that may not exist in PowerFactory's standard library
- **Action item**: Check with AEMO's model management team which IBR models are current and whether PowerFactory equivalents exist.

### 9.5 50 Hz vs. 60 Hz

Trivial but easy to miss: Australian system frequency is 50 Hz. PSSE examples from IEEE/ICSEG are often 60 Hz. PowerFactory defaults depend on the project settings. Ensure all test cases and translated models use the correct base frequency. Parameters like governor droop and PSS tuning are frequency-dependent.

### 9.6 Regulatory and Audit Requirements

AEMO operates under NER (National Electricity Rules) which require demonstrable model accuracy. Any translation tool must produce:
- **Parameter-by-parameter transformation log**: What went in, what came out, what was changed and why
- **Validation evidence**: Comparison of PSSE and PF simulation results
- **Traceability**: Every parameter must be traceable to a source (PSSE file, correction rule, engineering judgement)

This is a strong argument for Strategy B's approach (full control, auditable transformations) over Strategy A's black-box import.

---

## 10. Test Verification Methodology Critique

### Current Methodology (Shared Across All Strategies)

All three strategies use the same verification approach:
1. Run PSSE baseline → export time-series
2. Run PowerFactory → export time-series
3. Compare: Δδ ≤ 5°, ΔV ≤ 0.02 pu for 85%+ trajectory

### Critique

**10.1 Time-domain comparison alone is insufficient.** Time-domain comparison is necessary but not sufficient. Two models can produce similar time-domain responses with different internal states (e.g., wrong exciter parameters that happen to cancel out in the terminal voltage). Recommended verification hierarchy:

1. **Parameter-level verification** (most basic): Every input parameter matches expected value after transformation. Automated diff check.
2. **Power flow verification**: V, θ, P, Q at every bus. This catches network topology errors.
3. **Initial condition verification**: All state variables (fluxes, mechanical variables, controller states) at t=0 match PSSE's initial conditions. This catches model structure errors.
4. **Eigenvalue verification** (small-signal): Compare eigenvalues at the operating point. This is the most sensitive test for controller parameter accuracy.
5. **Time-domain verification** (large-signal): Compare transient response to a 3-phase fault. This catches non-linear effects (limits, saturation).

**10.2 The 85% trajectory metric is too lenient.** "85% of trajectory within tolerance" means 15% can be out of tolerance. For a 10-second simulation at 0.01s resolution, that's 150 time points with potentially large errors. For NEM regulatory purposes, this is insufficient. Recommendation:

- **All buses**: ΔV ≤ 0.01 pu, Δθ ≤ 1° for 95% of trajectory
- **Critical generators** (large machines, IBR): Δδ ≤ 3°, Δω ≤ 0.05 Hz for 98% of trajectory
- **No points** should exceed ΔV > 0.05 pu or Δδ > 15° at any time
- Time-domain comparison should use RMSE over the full trajectory, not just point-by-point tolerance

**10.3 Disturbance selection matters.** A single 3-phase fault is not enough. Different disturbances exercise different model features:

| Disturbance | What it tests |
|------------|---------------|
| 3-phase fault (5-6 cycle) | Large-signal stability, exciter ceiling, generator acceleration |
| Single-line-to-ground fault | Asymmetric effects (if modelled) |
| Generator trip | Governor response, frequency dynamics |
| Load step | Load model accuracy, frequency response |
| Line trip | Power flow redistribution, voltage recovery |
| Small signal (1% Vref step) | Exciter and PSS linearity, eigenvalue accuracy |

Recommendation: Use at least 3 disturbances for verification: (1) 3-phase fault, (2) generator trip, (3) small Vref step.

**10.4 Comparison at common time points.** PSSE and PowerFactory may use different time steps, producing results at different time points. Interpolation is needed before comparison. Use cubic spline interpolation to a common 0.01s grid. Document the interpolation method.

**10.5 No mention of numerical artefacts.** PSSE's fixed-step solver can produce numerical oscillations (especially around discontinuities like limit activation) that PowerFactory's variable-step solver smooths out. These artefacts shouldn't count as "discrepancies" — they're solver effects. The verification methodology should include a solver-effect tolerance band.

**10.6 Missing: cross-platform result file format.** PSSE exports to `.out`, `.csv`, or `.xlsx`. PowerFactory exports to `.csv`, `.elmfile`, or COMTRADE. Both need to be read into a common format for comparison. Recommendation: use HDF5 or Parquet as the intermediate comparison format with standardised column naming (bus_id, variable_name, time, value).

---

## Summary of Recommendations

| # | Recommendation | Priority | Strategy Affected |
|---|---------------|----------|------------------|
| 1 | **Start with Strategy A** — get results in 2 weeks | Critical | All |
| 2 | Build Strategy B as an extension of A, not a replacement | High | A, B |
| 3 | Defer Strategy C until B is working (C builds on B's registry) | Medium | C |
| 4 | Add eigenvalue comparison to verification methodology | High | All |
| 5 | Use PSSE (not ANDES) for baseline results | High | A |
| 6 | Add import log parsing as Step 0 of Strategy A | High | A |
| 7 | Hand-translate one model (ESST3A) to DSL before automating | Critical | B |
| 8 | Build PowerFactory API abstraction layer | High | A, B |
| 9 | Test CIM dynamics import gate before building CIM pipeline | Critical | C |
| 10 | Implement UDM tiers (1-4) with honest effort estimates | High | B |
| 11 | Treat PSCAD as validation source, not translation source | Medium | All |
| 12 | Treat SSAT as validation tool, not translation source | High | All |
| 13 | Add NEM-specific model mapping (AEMO naming → PSSE → PF) | High | All |
| 14 | Verify 50 Hz base frequency in all test cases | Low | All |
| 15 | Generate parameter-by-parameter transformation logs for audit | High | All |
| 16 | Tighten verification tolerances for regulatory use | Medium | All |
| 17 | Use multiple disturbances for verification | Medium | All |
| 18 | Isolate solver effects from model effects in comparison | Medium | All |

---

*End of critique. This document should be read alongside the three strategy documents and the research document. The critique is based on practical experience with cross-platform model translation and is intended to be constructive — all three strategies have merit, but their combination in a specific sequence (A → B → C) with the corrections above gives the best chance of success.*
