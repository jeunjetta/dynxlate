# Graph Report - dynaxlate  (2026-08-14)

## Corpus Check
- 25 files · ~25,840 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 418 nodes · 520 edges · 25 communities (22 shown, 3 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0b737bf9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TestDYRParser
- DSLGenerator
- comparison.py
- get_mapping
- TestStrategyDDocument
- PowerFactoryAdapter
- TestCIMGeneration
- TestANDESParserIntegration
- TestSystemIdentification
- parse_fortran_udm
- PSSEBaselineRunner
- TestIntegrationWithDynaxlate
- test_strategy_d.py
- Strategy A: Native PowerFactory Import + Automated Post-Processing
- TestMATLABAvailability
- DYRFile
- TestRoundTripNumerics
- Strategy D: MATLAB/Simulink as Universal Translation Hub
- TestSimulinkBlockMapping
- Dynxlate
- __init__.py
- dynaxlate

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
- **IBR and EMT Simulation Focus** — plans_emt_ibr_context, strategy_a_native, strategy_d_matlab [INFERRED 0.75]

## Communities (25 total, 3 thin omitted)

### Community 0 - "TestDYRParser"
Cohesion: 0.07
Nodes (19): parse_dyr(), Path, Parse a PSSE .dyr file into structured data. .dyr format: <bus> '<model_name>'…, fixture, Strategy A Test Harness: Native PowerFactory Import + Post-Processing. Tests…, IEEE 14-bus .dyr has expected model types., Parameters are correctly extracted from model entries., Bus-to-model mapping is correct. (+11 more)

### Community 1 - "DSLGenerator"
Cohesion: 0.09
Nodes (16): DSLGenerator, DSLModel, _lc(), DSL Generator: emit PowerFactory DSL model definitions from parsed Fortran…, Fortran logical-IF limiter -> min/max. IF (X .GT. LIM) X = LIM -> x = min(x,…, Return (lhs, rhs) in DSL form, or None if not translatable., Lowercase identifiers (DSL convention) but keep function names intact., Convenience: parse a Fortran UDM file and generate its DSL model. (+8 more)

### Community 2 - "comparison.py"
Cohesion: 0.10
Nodes (20): ndarray, compare_eigenvalues(), compare_powerflow(), compare_timeseries(), ComparisonMetric, ComparisonReport, Comparison Framework: Compare simulation results between PSSE and PowerFactory.…, Compare two time-series on a common time grid. Uses cubic spline interpolation… (+12 more)

### Community 3 - "get_mapping"
Cohesion: 0.07
Nodes (26): get_mapping(), list_supported_models(), _load_builtin_registry(), load_registry(), ModelMapping, ParameterMapping, Path, Model Registry: PSSE ↔ PowerFactory parameter mapping. YAML-driven mapping… (+18 more)

### Community 4 - "TestStrategyDDocument"
Cohesion: 0.06
Nodes (18): Document must mention digexfun interface for C DLL export., Document must mention FMU/FMI export pathway., Document must describe phased implementation plan., Document must include effort estimates., Document must describe integration with other strategies., Document should be substantial (at least 10KB of content)., Verify the strategy document is complete and well-structured., Strategy D document must exist. (+10 more)

### Community 5 - "PowerFactoryAdapter"
Cohesion: 0.08
Nodes (17): PFConnectionConfig, PowerFactoryAdapter, PowerFactory Adapter: Abstraction layer for PowerFactory Python API. Handles…, Import PSSE .raw/.dyr files via PowerFactory's native import. Args: raw_path:…, Run power flow on the active project. Returns bus voltage results., Run RMS (transient stability) simulation with a fault. Args: fault_bus: Bus…, PowerFactory connection configuration., Abstraction layer for PowerFactory Python API. Handles: - Application… (+9 more)

### Community 6 - "TestCIMGeneration"
Cohesion: 0.06
Nodes (20): fixture, Strategy C Test Harness: CIM Intermediate Format. Tests the IEC 61970 CIM-based…, Test generation of CIM XML from PSSE data., Generated CIM XML has correct root structure. Target: IEC 61970-452 CIM XML…, CIM XML includes power flow topology elements., CIM XML includes dynamics profile (61970-302) elements., Test CIM XML validation., Generated CIM XML passes IEC 61970 schema validation. (+12 more)

### Community 7 - "TestANDESParserIntegration"
Cohesion: 0.07
Nodes (20): fixture, Strategy B Test Harness: ANDES Parser + DSL Code Generation + Model Registry.…, Generated DSL code has valid structure., Test incremental verification: network → gens → exciters → governors., Network topology (no dynamics) produces correct power flow., Dynamic models converge during initialization., Test ANDES as the structured parser for .raw/.dyr files., Load IEEE 14-bus case via ANDES. (+12 more)

### Community 8 - "TestSystemIdentification"
Cohesion: 0.15
Nodes (9): fixture, Test the System Identification concept that enables UDM reverse- engineering…, Simulate a 'black box' UDM — a 3rd-order transfer function representing…, Generate step response test data., Generate chirp/sweep response., Recover transfer function from step response alone., Use chirp/sweep to identify frequency response. This demonstrates the MATLAB…, Classify an unknown UDM by its step response shape. (+1 more)

### Community 9 - "parse_fortran_udm"
Cohesion: 0.15
Nodes (11): Declaration, _is_comment(), _join_continuations(), parse_fortran_udm(), Path, Fortran UDM Parser: extract structure from PSSE user-defined model source. PSSE…, One CON/STATE/VAR/ICON allocation declared in the header comments., Fixed-form Fortran: any char in column 6 marks a continuation. (+3 more)

### Community 10 - "PSSEBaselineRunner"
Cohesion: 0.12
Nodes (13): PowerFlowResult, PSSEBaselineRunner, Path, PSSE baseline runner using ANDES. Produces Result Set 1: PSSE simulation…, Run small-signal test: voltage reference step on a generator. This exercises…, # TODO: implement via ANDES event system, Compute eigenvalues at the operating point for small-signal comparison., Time-series result from a simulation. (+5 more)

### Community 11 - "TestIntegrationWithDynaxlate"
Cohesion: 0.17
Nodes (7): Test that Strategy D integrates with the existing dynaxlate codebase., Strategy D uses the existing .dyr parser (or MATLAB equivalent)., Strategy D uses the existing model registry as its parameter map., Model registry has Simulink-relevant parameters., Strategy D's DSL generation can leverage existing code., Strategy D reuses the comparison framework., TestIntegrationWithDynaxlate

### Community 12 - "test_strategy_d.py"
Cohesion: 0.09
Nodes (14): cascade_tf(), Strategy D Test Harness: MATLAB/Simulink as Universal Translation Hub. Tests…, Cascade (series) multiple transfer functions by convolving numerator and…, Basic structural checks on MATLAB scripts in the strategy plan., Validate MATLAB .dyr parser function structure., Validate MATLAB function syntax in the plan., Validate MATLAB export function structures., All required MATLAB toolboxes should be documented. (+6 more)

### Community 13 - "Strategy A: Native PowerFactory Import + Automated Post-Processing"
Cohesion: 0.25
Nodes (9): ANDES Parser, IEC 61970-302 (CIM for Dynamics), Critique: PSSE-to-PowerFactory Dynamic Model Translation Strategies, EMT/IBR Context for Dynamic Model Translation, Research: PSSE ↔ PowerFactory Dynamic Model Translation, PowerFactory Python API, Strategy A: Native PowerFactory Import + Automated Post-Processing, Strategy B: ANDES-Based Parser + Modelica/DSL Code Generation (+1 more)

### Community 14 - "TestMATLABAvailability"
Cohesion: 0.28
Nodes (6): skipif, Check if MATLAB is available in the environment. These tests are marked as…, Check MATLAB is available via command line., Check MATPOWER can parse a PSSE .raw file., Test System Identification Toolbox tfest on known TF., TestMATLABAvailability

### Community 15 - "DYRFile"
Cohesion: 0.15
Nodes (10): DynamicModelEntry, DYRFile, DYR Parser: Extract dynamic model data from PSSE .dyr files. Lightweight parser…, A single dynamic model entry from a .dyr file., Convert positional parameters to a named dict using model registry., Parsed PSSE .dyr file., Get all entries for a specific model type., Get all dynamic models connected to a specific bus. (+2 more)

### Community 16 - "TestRoundTripNumerics"
Cohesion: 0.38
Nodes (4): Simulate both representations of USREXC and compare trajectories., Direct port of the Fortran MODE 2/3 equations (explicit Euler)., Evaluate the generated DSL equations numerically., TestRoundTripNumerics

### Community 17 - "Strategy D: MATLAB/Simulink as Universal Translation Hub"
Cohesion: 0.67
Nodes (3): MATPOWER (psse2mpc), Strategy D: MATLAB/Simulink as Universal Translation Hub, Fortran UDM Translation Problem

### Community 18 - "TestSimulinkBlockMapping"
Cohesion: 0.17
Nodes (7): Test that PSSE transfer function blocks map correctly to Simulink equivalents.…, ESST3A lead-lag block: PSSE TR → Simulink 1/(1+s*TR). The first block in ESST3A…, EXDC2 PI section maps to Simulink PID Controller. EXDC2 has a PI controller:…, TGOV1 governor: PSSE block chain maps to Simulink series. TGOV1: speed…, GENROU → ElmSym parameter transformation. PSSE GENROU uses operational…, IEEEST stabilizer: Simulink builds the same washout + phase comp. IEEEST:…, TestSimulinkBlockMapping

## Knowledge Gaps
- **8 isolated node(s):** `dynaxlate`, `Dynxlate`, `Research: PSSE ↔ PowerFactory Dynamic Model Translation`, `EMT/IBR Context for Dynamic Model Translation`, `ANDES Parser` (+3 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TestIntegrationWithDynaxlate` connect `TestIntegrationWithDynaxlate` to `DSLGenerator`, `test_strategy_d.py`?**
  _High betweenness centrality (0.416) - this node is a cross-community bridge._
- **Why does `DSLGenerator` connect `DSLGenerator` to `TestStrategyDDocument`, `TestSystemIdentification`, `parse_fortran_udm`, `TestIntegrationWithDynaxlate`, `test_strategy_d.py`, `TestMATLABAvailability`, `TestRoundTripNumerics`, `TestSimulinkBlockMapping`?**
  _High betweenness centrality (0.376) - this node is a cross-community bridge._
- **Why does `get_mapping()` connect `get_mapping` to `TestIntegrationWithDynaxlate`, `TestANDESParserIntegration`, `DYRFile`?**
  _High betweenness centrality (0.311) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `DSLGenerator` (e.g. with `FortranUDM` and `TestDSLGenerator`) actually correct?**
  _`DSLGenerator` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `PowerFactoryAdapter` (e.g. with `TestComparisonFramework` and `TestDYRParser`) actually correct?**
  _`PowerFactoryAdapter` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `get_mapping()` (e.g. with `.test_damping_correction_flagged()` and `.test_genrou_mapping()`) actually correct?**
  _`get_mapping()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `dynaxlate`, `Dynxlate`, `Research: PSSE ↔ PowerFactory Dynamic Model Translation` to the rest of the system?**
  _8 weakly-connected nodes found - possible documentation gaps or missing edges._