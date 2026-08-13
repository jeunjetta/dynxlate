# Graph Report - .  (2026-06-25)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 410 nodes · 505 edges · 24 communities (21 shown, 3 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0b737bf9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Simulation Comparison Framework|Simulation Comparison Framework]]
- [[_COMMUNITY_DSL Code Generator|DSL Code Generator]]
- [[_COMMUNITY_PSSE DYR Parser|PSSE DYR Parser]]
- [[_COMMUNITY_Model Parameter Registry|Model Parameter Registry]]
- [[_COMMUNITY_Strategy D Documentation|Strategy D Documentation]]
- [[_COMMUNITY_PowerFactory API Adapter|PowerFactory API Adapter]]
- [[_COMMUNITY_CIM Strategy Tests|CIM Strategy Tests]]
- [[_COMMUNITY_ANDES Strategy Tests|ANDES Strategy Tests]]
- [[_COMMUNITY_Simulink Strategy Tests|Simulink Strategy Tests]]
- [[_COMMUNITY_Fortran UDM Parser|Fortran UDM Parser]]
- [[_COMMUNITY_PSSE Baseline Runner|PSSE Baseline Runner]]
- [[_COMMUNITY_Integration Testing|Integration Testing]]
- [[_COMMUNITY_MATLAB Script Validation|MATLAB Script Validation]]
- [[_COMMUNITY_Translation Strategy Research|Translation Strategy Research]]
- [[_COMMUNITY_MATLAB Environment Checks|MATLAB Environment Checks]]
- [[_COMMUNITY_Documentation Reference Validation|Documentation Reference Validation]]
- [[_COMMUNITY_Numerical Round-Trip Testing|Numerical Round-Trip Testing]]
- [[_COMMUNITY_Translation Hub Concepts|Translation Hub Concepts]]
- [[_COMMUNITY_Package Initialization|Package Initialization]]
- [[_COMMUNITY_Translation Core|Translation Core]]
- [[_COMMUNITY_Project Root|Project Root]]

## God Nodes (most connected - your core abstractions)
1. `DSLGenerator` - 24 edges
2. `PowerFactoryAdapter` - 20 edges
3. `parse_fortran_udm()` - 19 edges
4. `TestStrategyDDocument` - 19 edges
5. `get_mapping()` - 17 edges
6. `translate_udm()` - 15 edges
7. `TestDSLGenerator` - 12 edges
8. `TestModelRegistry` - 12 edges
9. `TestPSSEBaseline` - 11 edges
10. `TestDYRParser` - 11 edges

## Surprising Connections (you probably didn't know these)
- `TestFortranParser` --uses--> `DSLGenerator`  [INFERRED]
  tests/test_fortran_udm.py → src/dynaxlate/dsl_generator.py
- `TestRoundTripNumerics` --uses--> `DSLGenerator`  [INFERRED]
  tests/test_fortran_udm.py → src/dynaxlate/dsl_generator.py
- `TestIntegrationWithDynaxlate` --uses--> `DSLGenerator`  [INFERRED]
  tests/test_strategy_d.py → src/dynaxlate/dsl_generator.py
- `TestMATLABAvailability` --uses--> `DSLGenerator`  [INFERRED]
  tests/test_strategy_d.py → src/dynaxlate/dsl_generator.py
- `TestMATLABScriptSyntax` --uses--> `DSLGenerator`  [INFERRED]
  tests/test_strategy_d.py → src/dynaxlate/dsl_generator.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Model Translation Strategies** — strategy_a_native, strategy_b_andes, strategy_c_cim, strategy_d_matlab [EXTRACTED 1.00]
- **IBR and EMT Simulation Focus** — emt_ibr_context, strategy_a_native, strategy_d_matlab [INFERRED 0.75]

## Communities (24 total, 3 thin omitted)

### Community 0 - "Simulation Comparison Framework"
Cohesion: 0.06
Nodes (27): compare_eigenvalues(), compare_powerflow(), compare_timeseries(), ComparisonMetric, ComparisonReport, Comparison Framework: Compare simulation results between PSSE and PowerFactory., Compare two time-series on a common time grid.      Uses cubic spline interpolat, Compare power flow results between PSSE and PowerFactory. (+19 more)

### Community 1 - "DSL Code Generator"
Cohesion: 0.09
Nodes (16): DSLGenerator, DSLModel, _lc(), DSL Generator: emit PowerFactory DSL model definitions from parsed Fortran UDMs., Fortran logical-IF limiter -> min/max.          IF (X .GT. LIM) X = LIM   ->   x, Return (lhs, rhs) in DSL form, or None if not translatable., Lowercase identifiers (DSL convention) but keep function names intact., Convenience: parse a Fortran UDM file and generate its DSL model. (+8 more)

### Community 2 - "PSSE DYR Parser"
Cohesion: 0.07
Nodes (21): DynamicModelEntry, DYRFile, parse_dyr(), DYR Parser: Extract dynamic model data from PSSE .dyr files.  Lightweight parser, A single dynamic model entry from a .dyr file., Convert positional parameters to a named dict using model registry., Parsed PSSE .dyr file., Get all entries for a specific model type. (+13 more)

### Community 3 - "Model Parameter Registry"
Cohesion: 0.08
Nodes (25): get_mapping(), list_supported_models(), _load_builtin_registry(), load_registry(), ModelMapping, ParameterMapping, Model Registry: PSSE ↔ PowerFactory parameter mapping.  YAML-driven mapping tabl, Single parameter mapping from PSSE to PowerFactory. (+17 more)

### Community 4 - "Strategy D Documentation"
Cohesion: 0.06
Nodes (18): Document must mention digexfun interface for C DLL export., Document must mention FMU/FMI export pathway., Document must describe phased implementation plan., Document must include effort estimates., Document must describe integration with other strategies., Document should be substantial (at least 10KB of content)., Verify the strategy document is complete and well-structured., Strategy D document must exist. (+10 more)

### Community 5 - "PowerFactory API Adapter"
Cohesion: 0.08
Nodes (17): PFConnectionConfig, PowerFactoryAdapter, PowerFactory Adapter: Abstraction layer for PowerFactory Python API.  Handles ap, Import PSSE .raw/.dyr files via PowerFactory's native import.          Args:, Run power flow on the active project.          Returns bus voltage results., Run RMS (transient stability) simulation with a fault.          Args:, PowerFactory connection configuration., Abstraction layer for PowerFactory Python API.      Handles:     - Application s (+9 more)

### Community 6 - "CIM Strategy Tests"
Cohesion: 0.06
Nodes (19): Strategy C Test Harness: CIM Intermediate Format.  Tests the IEC 61970 CIM-based, Test generation of CIM XML from PSSE data., Generated CIM XML has correct root structure.          Target: IEC 61970-452 CIM, CIM XML includes power flow topology elements., CIM XML includes dynamics profile (61970-302) elements., Test CIM XML validation., Generated CIM XML passes IEC 61970 schema validation., CIM XML passes SHACL shape validation. (+11 more)

### Community 7 - "ANDES Strategy Tests"
Cohesion: 0.07
Nodes (19): Strategy B Test Harness: ANDES Parser + DSL Code Generation + Model Registry.  T, Generated DSL code has valid structure., Test incremental verification: network → gens → exciters → governors., Network topology (no dynamics) produces correct power flow., Dynamic models converge during initialization., Test ANDES as the structured parser for .raw/.dyr files., Load IEEE 14-bus case via ANDES., ANDES extracts bus data correctly. (+11 more)

### Community 8 - "Simulink Strategy Tests"
Cohesion: 0.07
Nodes (18): cascade_tf(), Strategy D Test Harness: MATLAB/Simulink as Universal Translation Hub.  Tests th, Test that PSSE transfer function blocks map correctly to Simulink     equivalent, ESST3A lead-lag block: PSSE TR → Simulink 1/(1+s*TR).          The first block i, EXDC2 PI section maps to Simulink PID Controller.          EXDC2 has a PI contro, TGOV1 governor: PSSE block chain maps to Simulink series.          TGOV1: speed, GENROU → ElmSym parameter transformation.          PSSE GENROU uses operational, IEEEST stabilizer: Simulink builds the same washout + phase comp.          IEEES (+10 more)

### Community 9 - "Fortran UDM Parser"
Cohesion: 0.16
Nodes (10): Declaration, _is_comment(), _join_continuations(), parse_fortran_udm(), Fortran UDM Parser: extract structure from PSSE user-defined model source.  PSSE, One CON/STATE/VAR/ICON allocation declared in the header comments., Fixed-form Fortran: any char in column 6 marks a continuation., Parse a PSSE Fortran UDM source file into structured form. (+2 more)

### Community 10 - "PSSE Baseline Runner"
Cohesion: 0.14
Nodes (12): PowerFlowResult, PSSEBaselineRunner, PSSE baseline runner using ANDES.  Produces Result Set 1: PSSE simulation result, Run small-signal test: voltage reference step on a generator.          This exer, # TODO: implement via ANDES event system, Compute eigenvalues at the operating point for small-signal comparison., Time-series result from a simulation., Power flow result at all buses. (+4 more)

### Community 11 - "Integration Testing"
Cohesion: 0.17
Nodes (7): Test that Strategy D integrates with the existing dynaxlate codebase., Strategy D uses the existing .dyr parser (or MATLAB equivalent)., Strategy D uses the existing model registry as its parameter map., Model registry has Simulink-relevant parameters., Strategy D's DSL generation can leverage existing code., Strategy D reuses the comparison framework., TestIntegrationWithDynaxlate

### Community 12 - "MATLAB Script Validation"
Cohesion: 0.20
Nodes (6): Basic structural checks on MATLAB scripts in the strategy plan., Validate MATLAB .dyr parser function structure., Validate MATLAB function syntax in the plan., Validate MATLAB export function structures., All required MATLAB toolboxes should be documented., TestMATLABScriptSyntax

### Community 13 - "Translation Strategy Research"
Cohesion: 0.25
Nodes (9): ANDES Parser, IEC 61970-302 (CIM for Dynamics), Critique: PSSE-to-PowerFactory Dynamic Model Translation Strategies, EMT/IBR Context for Dynamic Model Translation, PowerFactory Python API, Research: PSSE ↔ PowerFactory Dynamic Model Translation, Strategy A: Native PowerFactory Import + Automated Post-Processing, Strategy B: ANDES-Based Parser + Modelica/DSL Code Generation (+1 more)

### Community 14 - "MATLAB Environment Checks"
Cohesion: 0.25
Nodes (5): Check if MATLAB is available in the environment.      These tests are marked as, Check MATLAB is available via command line., Check MATPOWER can parse a PSSE .raw file., Test System Identification Toolbox tfest on known TF., TestMATLABAvailability

### Community 15 - "Documentation Reference Validation"
Cohesion: 0.25
Nodes (5): Verify MathWorks references in the strategy document are valid., Strategy document references mathworks.com sufficiently., Strategy references MATLAB Central / community., Strategy references DIgSILENT documentation., TestReferences

### Community 16 - "Numerical Round-Trip Testing"
Cohesion: 0.38
Nodes (4): Simulate both representations of USREXC and compare trajectories., Direct port of the Fortran MODE 2/3 equations (explicit Euler)., Evaluate the generated DSL equations numerically., TestRoundTripNumerics

### Community 17 - "Translation Hub Concepts"
Cohesion: 0.67
Nodes (3): MATPOWER (psse2mpc), Strategy D: MATLAB/Simulink as Universal Translation Hub, Fortran UDM Translation Problem

## Knowledge Gaps
- **8 isolated node(s):** `dynaxlate`, `Dynxlate`, `Research: PSSE ↔ PowerFactory Dynamic Model Translation`, `EMT/IBR Context for Dynamic Model Translation`, `ANDES Parser` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `parse_dyr()` connect `PSSE DYR Parser` to `Integration Testing`, `CIM Strategy Tests`, `ANDES Strategy Tests`?**
  _High betweenness centrality (0.336) - this node is a cross-community bridge._
- **Why does `TestIntegrationWithDynaxlate` connect `Integration Testing` to `Simulink Strategy Tests`, `DSL Code Generator`?**
  _High betweenness centrality (0.310) - this node is a cross-community bridge._
- **Why does `DSLGenerator` connect `DSL Code Generator` to `Strategy D Documentation`, `Simulink Strategy Tests`, `Fortran UDM Parser`, `Integration Testing`, `MATLAB Script Validation`, `MATLAB Environment Checks`, `Documentation Reference Validation`, `Numerical Round-Trip Testing`?**
  _High betweenness centrality (0.296) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `DSLGenerator` (e.g. with `FortranUDM` and `TestDSLGenerator`) actually correct?**
  _`DSLGenerator` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `PowerFactoryAdapter` (e.g. with `TestComparisonFramework` and `TestDYRParser`) actually correct?**
  _`PowerFactoryAdapter` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `get_mapping()` (e.g. with `.test_damping_correction_flagged()` and `.test_genrou_mapping()`) actually correct?**
  _`get_mapping()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `dynaxlate`, `Dynaxlate — Dynamic Model Translation between Power System Simulation Formats.`, `Comparison Framework: Compare simulation results between PSSE and PowerFactory.` to the rest of the system?**
  _183 weakly-connected nodes found - possible documentation gaps or missing edges._