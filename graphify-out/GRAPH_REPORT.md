# Graph Report - dynxlate  (2026-08-15)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 418 nodes · 504 edges · 25 communities (21 shown, 4 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 29 edges (avg confidence: 0.76)
- Token cost: 1,811 input · 260 output

## Graph Freshness
- Built from commit: `ffc555bf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Model Parameter Mapping
- PSSE DYR Parser
- Strategy D Documentation
- CIM Export Strategy
- MATLAB Strategy Harness
- DSL Code Generator
- PowerFactory API Adapter
- ANDES Parser Strategy
- Fortran UDM Parser
- Simulation Comparison Framework
- PSSE Baseline Runner
- ANDES Baseline Testing
- System Identification Testing
- Simulink Block Mapping
- Strategy Integration Tests
- Translation Strategy Overview
- Numerical Round-Trip Validation
- MATLAB Translation Hub
- Package Initialization
- Dynaxlate Core
- Interoperability Research
- Project Documentation

## God Nodes (most connected - your core abstractions)
1. `parse_fortran_udm()` - 19 edges
2. `TestStrategyDDocument` - 18 edges
3. `get_mapping()` - 17 edges
4. `DSLGenerator` - 16 edges
5. `PowerFactoryAdapter` - 16 edges
6. `translate_udm()` - 14 edges
7. `TestDSLGenerator` - 12 edges
8. `TestModelRegistry` - 11 edges
9. `TestDYRParser` - 10 edges
10. `TestPSSEBaseline` - 10 edges

## Surprising Connections (you probably didn't know these)
- `TestIntegrationWithDynaxlate` --uses--> `DSLGenerator`  [INFERRED]
  tests/test_strategy_d.py → src/dynxlate/dsl_generator.py
- `TestDSLGenerator` --uses--> `DSLGenerator`  [INFERRED]
  tests/test_fortran_udm.py → src/dynxlate/dsl_generator.py
- `TestPowerFactoryAdapter` --uses--> `PowerFactoryAdapter`  [INFERRED]
  tests/test_strategy_a.py → src/dynxlate/pf_adapter.py
- `DSLGenerator` --uses--> `FortranUDM`  [INFERRED]
  src/dynxlate/dsl_generator.py → src/dynxlate/fortran_parser.py
- `translate_udm()` --calls--> `parse_fortran_udm()`  [EXTRACTED]
  src/dynxlate/dsl_generator.py → src/dynxlate/fortran_parser.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Dynamic Model Translation Strategies** — plans_strategy_a_native_import, plans_strategy_b_andes_dsl_generator, plans_strategy_c_cim_intermediate, plans_strategy_d_matlab_simulink_translator [EXTRACTED 1.00]
- **Cross-Platform Verification Methodology** — plans_critique, plans_emt_ibr_context, plans_strategy_a_native_import [INFERRED 0.85]

## Communities (25 total, 4 thin omitted)

### Community 0 - "Model Parameter Mapping"
Cohesion: 0.07
Nodes (26): get_mapping(), list_supported_models(), _load_builtin_registry(), load_registry(), ModelMapping, ParameterMapping, Path, Model Registry: PSSE ↔ PowerFactory parameter mapping. YAML-driven mapping… (+18 more)

### Community 1 - "PSSE DYR Parser"
Cohesion: 0.07
Nodes (21): DynamicModelEntry, DYRFile, parse_dyr(), Path, DYR Parser: Extract dynamic model data from PSSE .dyr files. Lightweight parser…, A single dynamic model entry from a .dyr file., Convert positional parameters to a named dict using model registry., Parsed PSSE .dyr file. (+13 more)

### Community 2 - "Strategy D Documentation"
Cohesion: 0.06
Nodes (18): Document must mention digexfun interface for C DLL export., Document must mention FMU/FMI export pathway., Document must describe phased implementation plan., Document must include effort estimates., Document must describe integration with other strategies., Document should be substantial (at least 10KB of content)., Verify the strategy document is complete and well-structured., Strategy D document must exist. (+10 more)

### Community 3 - "CIM Export Strategy"
Cohesion: 0.06
Nodes (20): fixture, Strategy C Test Harness: CIM Intermediate Format. Tests the IEC 61970 CIM-based…, Test generation of CIM XML from PSSE data., Generated CIM XML has correct root structure. Target: IEC 61970-452 CIM XML…, CIM XML includes power flow topology elements., CIM XML includes dynamics profile (61970-302) elements., Test CIM XML validation., Generated CIM XML passes IEC 61970 schema validation. (+12 more)

### Community 4 - "MATLAB Strategy Harness"
Cohesion: 0.07
Nodes (20): skipif, cascade_tf(), Strategy D Test Harness: MATLAB/Simulink as Universal Translation Hub. Tests…, Cascade (series) multiple transfer functions by convolving numerator and…, Basic structural checks on MATLAB scripts in the strategy plan., Validate MATLAB .dyr parser function structure., Validate MATLAB function syntax in the plan., Validate MATLAB export function structures. (+12 more)

### Community 5 - "DSL Code Generator"
Cohesion: 0.10
Nodes (13): DSLGenerator, DSLModel, _lc(), Fortran logical-IF limiter -> min/max. IF (X .GT. LIM) X = LIM -> x = min(x,…, Return (lhs, rhs) in DSL form, or None if not translatable., Lowercase identifiers (DSL convention) but keep function names intact., Convenience: parse a Fortran UDM file and generate its DSL model., Generated PowerFactory DSL model. (+5 more)

### Community 6 - "PowerFactory API Adapter"
Cohesion: 0.08
Nodes (17): PFConnectionConfig, PowerFactoryAdapter, PowerFactory Adapter: Abstraction layer for PowerFactory Python API. Handles…, Import PSSE .raw/.dyr files via PowerFactory's native import. Args: raw_path:…, Run power flow on the active project. Returns bus voltage results., Run RMS (transient stability) simulation with a fault. Args: fault_bus: Bus…, PowerFactory connection configuration., Abstraction layer for PowerFactory Python API. Handles: - Application… (+9 more)

### Community 7 - "ANDES Parser Strategy"
Cohesion: 0.07
Nodes (20): fixture, Strategy B Test Harness: ANDES Parser + DSL Code Generation + Model Registry.…, Generated DSL code has valid structure., Test incremental verification: network → gens → exciters → governors., Network topology (no dynamics) produces correct power flow., Dynamic models converge during initialization., Test ANDES as the structured parser for .raw/.dyr files., Load IEEE 14-bus case via ANDES. (+12 more)

### Community 8 - "Fortran UDM Parser"
Cohesion: 0.11
Nodes (14): DSL Generator: emit PowerFactory DSL model definitions from parsed Fortran…, Declaration, FortranUDM, _is_comment(), _join_continuations(), parse_fortran_udm(), Path, Fortran UDM Parser: extract structure from PSSE user-defined model source. PSSE… (+6 more)

### Community 9 - "Simulation Comparison Framework"
Cohesion: 0.09
Nodes (21): ndarray, compare_eigenvalues(), compare_powerflow(), compare_timeseries(), ComparisonMetric, ComparisonReport, Comparison Framework: Compare simulation results between PSSE and PowerFactory.…, Compare two time-series on a common time grid. Uses cubic spline interpolation… (+13 more)

### Community 10 - "PSSE Baseline Runner"
Cohesion: 0.12
Nodes (13): PowerFlowResult, PSSEBaselineRunner, Path, PSSE baseline runner using ANDES. Produces Result Set 1: PSSE simulation…, Run small-signal test: voltage reference step on a generator. This exercises…, # TODO: implement via ANDES event system, Compute eigenvalues at the operating point for small-signal comparison., Time-series result from a simulation. (+5 more)

### Community 11 - "ANDES Baseline Testing"
Cohesion: 0.16
Nodes (7): fixture, Test PSSE baseline simulation via ANDES., ANDES successfully loads .raw power flow file., ANDES successfully loads .dyr with standard models., Power flow converges on the test case., Power flow produces physically reasonable results., TestPSSEBaseline

### Community 12 - "System Identification Testing"
Cohesion: 0.15
Nodes (9): fixture, Test the System Identification concept that enables UDM reverse- engineering…, Simulate a 'black box' UDM — a 3rd-order transfer function representing…, Generate step response test data., Generate chirp/sweep response., Recover transfer function from step response alone., Use chirp/sweep to identify frequency response. This demonstrates the MATLAB…, Classify an unknown UDM by its step response shape. (+1 more)

### Community 13 - "Simulink Block Mapping"
Cohesion: 0.17
Nodes (7): Test that PSSE transfer function blocks map correctly to Simulink equivalents.…, ESST3A lead-lag block: PSSE TR → Simulink 1/(1+s*TR). The first block in ESST3A…, EXDC2 PI section maps to Simulink PID Controller. EXDC2 has a PI controller:…, TGOV1 governor: PSSE block chain maps to Simulink series. TGOV1: speed…, GENROU → ElmSym parameter transformation. PSSE GENROU uses operational…, IEEEST stabilizer: Simulink builds the same washout + phase comp. IEEEST:…, TestSimulinkBlockMapping

### Community 14 - "Strategy Integration Tests"
Cohesion: 0.17
Nodes (7): Test that Strategy D integrates with the existing dynxlate codebase., Strategy D uses the existing .dyr parser (or MATLAB equivalent)., Strategy D uses the existing model registry as its parameter map., Model registry has Simulink-relevant parameters., Strategy D's DSL generation can leverage existing code., Strategy D reuses the comparison framework., TestIntegrationWithDynaxlate

### Community 15 - "Translation Strategy Overview"
Cohesion: 0.22
Nodes (9): ANDES Parser, IEC 61970-302 (CIM Dynamics), Critique: PSSE-to-PowerFactory Strategies, EMT/IBR Context, Strategy A: Native Import, Strategy B: ANDES-Based Parser, Strategy C: CIM Intermediate, PowerFactory (.pfd/DSL) (+1 more)

### Community 16 - "Numerical Round-Trip Validation"
Cohesion: 0.38
Nodes (4): Simulate both representations of USREXC and compare trajectories., Direct port of the Fortran MODE 2/3 equations (explicit Euler)., Evaluate the generated DSL equations numerically., TestRoundTripNumerics

### Community 17 - "MATLAB Translation Hub"
Cohesion: 0.67
Nodes (3): MATPOWER, Strategy D: MATLAB/Simulink Hub, Fortran UDM Translation

## Knowledge Gaps
- **10 isolated node(s):** `dynxlate`, `ANDES Parser`, `IEC 61970-302 (CIM Dynamics)`, `PowerFactory (.pfd/DSL)`, `PSSE (.raw/.dyr)` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TestIntegrationWithDynaxlate` connect `Strategy Integration Tests` to `MATLAB Strategy Harness`, `DSL Code Generator`?**
  _High betweenness centrality (0.487) - this node is a cross-community bridge._
- **Why does `get_mapping()` connect `Model Parameter Mapping` to `PSSE DYR Parser`, `Strategy Integration Tests`, `ANDES Parser Strategy`?**
  _High betweenness centrality (0.309) - this node is a cross-community bridge._
- **Why does `parse_dyr()` connect `PSSE DYR Parser` to `CIM Export Strategy`, `Strategy Integration Tests`, `ANDES Parser Strategy`?**
  _High betweenness centrality (0.277) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `get_mapping()` (e.g. with `.test_damping_correction_flagged()` and `.test_genrou_mapping()`) actually correct?**
  _`get_mapping()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `DSLGenerator` (e.g. with `FortranUDM` and `TestDSLGenerator`) actually correct?**
  _`DSLGenerator` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `PowerFactoryAdapter` (e.g. with `TestPowerFactoryAdapter` and `.test_adapter_instantiation()`) actually correct?**
  _`PowerFactoryAdapter` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `dynxlate`, `ANDES Parser`, `IEC 61970-302 (CIM Dynamics)` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._