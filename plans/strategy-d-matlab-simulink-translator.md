# Strategy D: MATLAB/Simulink as Universal Translation Hub

## Overview

Use MATLAB and Simulink (MathWorks, au.mathworks.com) as the **intermediate translation environment** between PSSE and PowerFactory. MATLAB parses PSSE `.raw`/`.dyr` files (via MATPOWER + custom `.dyr` parser), reconstructs the dynamic models as Simulink block diagrams, validates them by simulation, then exports to PowerFactory via DSL code generation, C-code DLL (via digexfun), FMU export, or direct Python API calls.

## Rationale

MATLAB/Simulink occupies a unique position in the translation toolchain:

1. **Block diagram paradigm match** — Simulink, PSSE (block diagrams), and PowerFactory DSL all use the same fundamental abstraction: transfer functions, lead-lag blocks, gains, limits, washout filters wired together. A GENROU → ESST3A → TGOV1 chain in PSSE maps structurally to the same Simulink model.

2. **MATPOWER reads PSSE `.raw` natively** — MATPOWER's `psse2mpc()` and `psse_parse()` parse PSSE power flow files into MATLAB structs with full bus/branch/generator topology. No intermediate parser needed.

3. **System Identification Toolbox solves the UDM problem** — Fortran UDMs (the hardest category in all other strategies) can be reverse-engineered by running the compiled UDM in PSSE with controlled test signals, measuring input/output, and identifying the transfer function using MATLAB's system identification. This is the only strategy with a *practical* path for UDMs without source code.

4. **Simulink Coder → C DLL → PowerFactory digexfun** — Simulink models can be compiled to C code, then linked as a DLL that PowerFactory calls through its `digexfun` external function interface. This bypasses DSL entirely for complex models.

5. **FMU/FMI export** — Simulink exports Functional Mock-up Units. PowerFactory can import FMUs for co-simulation. This is a standardised, tool-agnostic bridge.

6. **MATLAB ↔ Python ↔ PowerFactory API** — MATLAB has built-in Python interoperability (`py.` namespace). This means MATLAB can directly drive PowerFactory's Python API to create projects, set parameters, and run simulations — all from the same script that parsed the PSSE data.

7. **Co-simulation verification** — PowerFactory's `digexfun` interface allows a DSL model to call MATLAB in engine mode at each timestep. This enables side-by-side comparison without needing a full translation: run the original PSSE-model-as-Simulink alongside the PowerFactory-native-equivalent and compare timestep-by-timestep.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MATLAB Environment                        │
│                                                             │
│  PSSE (.raw + .dyr)                                         │
│       │                                                     │
│       ▼                                                     │
│  MATPOWER (psse2mpc) ← power flow parsed                    │
│  Custom .dyr parser   ← dynamic model parameters            │
│       │                                                     │
│       ▼                                                     │
│  Model Registry (MATLAB structs/classes)                    │
│  ├── Network topology (buses, lines, xfmrs, loads)          │
│  ├── Generator parameters (GENROU, GENCLS, ...)             │
│  ├── Exciter parameters (ESST3A, EXDC2, EXST1, ...)         │
│  ├── Governor parameters (TGOV1, IEEEG1, ...)               │
│  ├── Stabilizer parameters (IEEEST, ST2CUT, ...)            │
│  └── Renewable plant parameters (REGC_A, REEC_B, ...)       │
│       │                                                     │
│       ├──────────────────────────────────────────────┐      │
│       │                                              │      │
│       ▼                                              ▼      │
│  Simulink Model Builder                       System ID    │
│  └── Generate .slx from block library            Toolbox    │
│      for each model component                   └── For     │
│                                                  UDMs:      │
│       │                                          test →     │
│       │                                          identify   │
│       ▼                                          → rebuild  │
│  Simulation Verification                                     │
│  └── Same disturbance → compare Simulink vs PSSE            │
│      (validate translation BEFORE PowerFactory)             │
│       │                                                     │
│       └──────────────┬───────────────────────┐              │
│                      │                       │              │
│                      ▼                       ▼              │
│  Export Path 1:                     Export Path 2:          │
│  DSL Code Generation                C Code + DLL            │
│  └── Translate Simulink             └── Simulink Coder      │
│      blocks → DSL source               → .c/.h files        │
│  └── Write DSL files for            └── Compile → .dll      │
│      PowerFactory import            └── PowerFactory        │
│                                           digexfun call     │
│                      │                                      │
│                      ▼                                      │
│  Export Path 3: FMU Export                                  │
│  └── Simulink → .fmu (co-simulation or model-exchange)     │
│  └── PowerFactory imports FMU directly                     │
│                      │                                      │
│                      ▼                                      │
│  Export Path 4: MATLAB → Python API                         │
│  └── MATLAB calls py.powerfactory → creates .pfd project   │
│  └── Sets parameters from registry → runs, compares        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 PowerFactory (.pfd)                          │
│  ├── DSL models imported (Path 1)                            │
│  ├── External DLL models (Path 2)                            │
│  ├── FMU co-simulation models (Path 3)                      │
│  └── Python-API-built project (Path 4)                      │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. MATPOWER Integration (.raw Parser)

MATPOWER provides `psse2mpc()` which converts PSSE `.raw` (v30–35) to MATLAB `mpc` structs:

```
mpc = psse2mpc('ieee14.raw');

% Access parsed data:
mpc.bus          % [bus_i, type, Pd, Qd, Gs, Bs, area, Vm, Va, ...]
mpc.gen          % [bus, Pg, Qg, Qmax, Qmin, Vg, mBase, ...]
mpc.branch       % [from, to, r, x, b, rateA, rateB, ...]
```

### 2. Custom `.dyr` Parser (MATLAB)

PSSE `.dyr` is line-based plain text — straightforward to parse in MATLAB with regex:

```matlab
% src/parse_dyr.m
function models = parse_dyr(filename)
    % Returns struct array of dynamic models
    %
    % models(i).bus       = bus number
    % models(i).name      = model name (e.g. 'GENROU', 'ESST3A')
    % models(i).id        = model ID ('1', '2', etc.)
    % models(i).params    = numeric array of parameters
    % models(i).raw_line  = original text line
    %
    fid = fopen(filename, 'r');
    lines = strip(splitlines(fscanf(fid, '%c')));
    fclose(fid);
    
    pat = '^\s*(?<bus>\d+)\s+''(?<name>[^'']+)''\s+''(?<id>[^'']*)''\s*(?<params>.*?)\s*/$';
    models = struct('bus', {}, 'name', {}, 'id', {}, 'params', {}, 'raw_line', {});
    
    for i = 1:length(lines)
        line = strtrim(lines{i});
        if isempty(line) || startsWith(line, '!') || startsWith(line, '--')
            continue;
        end
        % ... parse with regexp ...
    end
end
```

### 3. Model Registry (MATLAB Class)

A MATLAB class hierarchy that maps PSSE model parameters to both Simulink block parameters and PowerFactory DSL parameters:

```matlab
% src/ModelRegistry.m
classdef ModelRegistry < handle
    properties
        models = containers.Map();  % model_name -> ModelMapping
    end
    
    methods
        function reg = ModelRegistry()
            reg = reg.register_standard_models();
        end
        
        function mapping = lookup(reg, name)
            % Lookup by name, with fuzzy match for NEM-specific naming
            if reg.models.isKey(name)
                mapping = reg.models(name);
            else
                mapping = reg.fuzzy_match(name);
            end
        end
    end
    
    methods (Access = private)
        function reg = register_standard_models(reg)
            % GENROU mapping
            reg.models('GENROU') = ModelMapping(...
                'psse_name', 'GENROU', ...
                'pf_name', 'ElmSym', ...
                'simulink_lib', 'Machines/Simplified Synchronous Machine', ...
                'params', {...
                    ParamMapping('Tpdo',  'T',   1.0,  'd-axis transient open-circuit'), ...
                    ParamMapping('Tppdo', 'T',   1.0,  'd-axis subtransient open-circuit'), ...
                    ParamMapping('Tpqo',  'T',   1.0,  'q-axis transient open-circuit'), ...
                    ParamMapping('Tppqo', 'T',   1.0,  'q-axis subtransient open-circuit'), ...
                    ParamMapping('H',     'H',   1.0,  'inertia'), ...
                    ParamMapping('D',     'Damp', 1.0,  'damping (see correction note)'), ...
                    ParamMapping('Xd',    'Xd',  1.0,  'd-axis synchronous reactance'), ...
                    ParamMapping('Xq',    'Xq',  1.0,  'q-axis synchronous reactance'), ...
                    % ... remaining GENROU parameters ...
                }, ...
                'corrections', {'Damping: PSSE D=load damping, PF D=rotor friction', ...
                                'Saturation model differs between platforms', ...
                                'Step-up transformer: explicit in PF, implicit in PSSE'}, ...
                'sim_domain', 'rms');
            
            % ESST3A, EXDC2, TGOV1, etc. similarly...
        end
    end
end
```

### 4. Simulink Model Builder

Generates Simulink block diagrams from parsed model data:

```matlab
% src/build_simulink_model.m
function build_simulink_model(models, output_name)
    % Create Simulink model from parsed PSSE dynamic models
    %
    % For each generator bus, build:
    %   Generator block (GENROU → Synchronous Machine)
    %   + Exciter block (ESST3A → transfer function chain)
    %   + Governor block (TGOV1 → transfer function chain)
    %   + PSS block (IEEEST → transfer function chain)
    %   + Wired together as composite model
    
    % PSSE ESST3A block diagram is: lead-lag → lag → PI → limits
    % Simulink equivalent: TransferFcn → TransferFcn → PID Controller → Saturation
    
    new_system(output_name);
    % ... add blocks programmatically ...
    % ... wire connections ...
    % ... set parameters ...
    
    save_system(output_name);
end
```

For a standard ESST3A exciter, the Simulink block diagram would look like:

```
Vref ──(+)──[1+sTR]──[KC]──[1+sTB/1+sTC]──[K_A]──[Vmin,Vmax]── Efd
        │                                      │
        └──Vt ─────────────────────────────────┘  (feedback)
```

### 5. System Identification for UDMs (The UDM Game-Changer)

The single biggest advantage of this strategy: **reverse-engineering UDMs without source code**.

```matlab
% src/identify_udm.m
function identified_model = identify_udm(udm_name, test_data_file)
    % UDM Black-Box Identification
    %
    % Given a Fortran UDM compiled as .dll:
    % 1. Run UDM in PSSE with systematic test signals
    %    - Step input (5% Vref step)
    %    - Frequency ramp (±0.5 Hz over 10s)
    %    - Voltage dip (0.9 pu for 100ms)
    %    - Chirp/sweep signal (0.1-10 Hz over 20s)
    %
    % 2. Capture input/output time-series
    %    - Input: Vt, Vref, Ifd (depending on model type)
    %    - Output: Efd, Pmech, Vstab (depending on model type)
    %
    % 3. Import into System Identification Toolbox
    
    data = iddata(test_data.output, test_data.input, test_data.Ts);
    
    % Try linear model identification first
    sys_linear = tfest(data, np=3, nz=2);  % 3-pole, 2-zero transfer function
    
    % Validate against other test signals
    compare(test_data_validation, sys_linear);
    
    % If linear fit is poor, try Hammerstein-Wiener (nonlinear)
    if sys_linear.Report.Fit.FitPercent < 85
        sys_nonlinear = nlhw(data, [3 2], 'wavenet', 'saturation');
        identified_model = sys_nonlinear;
    else
        identified_model = sys_linear;
    end
    
    % 4. Export identified model:
    %    - As Simulink block (for further validation)
    %    - As C code via Simulink Coder (for PowerFactory DLL)
    %    - Parameter set for equivalent standard model (if it matches)
end
```

**Test Signal Protocol for UDM Identification:**

| Signal | Duration | Purpose | What it Excites |
|--------|----------|---------|-----------------|
| Step (+5% Vref) | 5s | Transient response | Time constants, gain |
| Frequency ramp (50→51 Hz) | 10s | Governor response | Droop, deadband |
| Voltage dip (0.9 pu, 100ms) | 3s | Exciter ceiling | Limits, saturation |
| Chirp (0.1–10 Hz, 20s) | 20s | Frequency response | Full transfer function |
| Pseudo-random binary | 30s | Non-linear dynamics | Hysteresis, switching |

### 6. PowerFactory Export Paths

#### Path 1: DSL Code Generation

Generate PowerFactory DSL from validated Simulink block structure:

```matlab
% src/export_to_pf_dsl.m
function dsl_code = export_to_pf_dsl(simulink_model_name)
    % Traverse Simulink block diagram → generate DSL
    % 
    % For each block in the Simulink model:
    %   TransferFcn → DSL block: inc(transfer_function)
    %   Saturation  → DSL block: lim(Vmin, Vmax)
    %   Gain        → DSL block: kp(gain)
    %   Sum         → DSL block: sum(sum_inputs)
    %   PID         → DSL block: pi(Kp, Ki)
    %
    load_system(simulink_model_name);
    blocks = find_system(simulink_model_name, 'LookUnderMasks', 'all', ...
                         'Type', 'block');
    
    dsl_code = sprintf('class %s {\n', simulink_model_name);
    dsl_code = [dsl_code, '  input Vt, Vref;\n'];
    dsl_code = [dsl_code, '  output Efd;\n'];
    
    for i = 1:length(blocks)
        block_type = get_param(blocks{i}, 'BlockType');
        dsl_code = [dsl_code, translate_block_to_dsl(blocks{i}, block_type)];
    end
    
    dsl_code = [dsl_code, '}\n'];
end
```

#### Path 2: C Code → DLL → PowerFactory digexfun

For models too complex for DSL (UTM tier):

```matlab
% src/export_to_pf_dll.m
function export_to_pf_dll(simulink_model_name)
    % 1. Configure Simulink Coder
    cs = getActiveConfigSet(simulink_model_name);
    set_param(cs, 'GenerateCodeOnly', 'on');
    set_param(cs, 'TargetLang', 'C');
    set_param(cs, 'SystemTargetFile', 'ert.tlc');  % Embedded Real-Time
    
    % 2. Generate C code
    rtwbuild(simulink_model_name);
    
    % 3. The generated code exports step() and initialize() functions
    %    These can be wrapped as a PowerFactory digexfun DLL.
    %
    %    PowerFactory digexfun interface expects:
    %      SUBROUTINE DIGEXFUN(I, U, Y, STATUS)
    %      where I = number of inputs, U = input array,
    %            Y = output array, STATUS = error status
    %
    %    Generate C wrapper:
    wrapper = sprintf([
        '#include "rtwtypes.h"\n'
        '#include "%s.h"\n\n'
        'void digexfun_(int *I, double *U, double *Y, int *STATUS) {\n'
        '  static %sModelClass model;\n'
        '  static int initialized = 0;\n'
        '  if (!initialized) {\n'
        '    model.initialize();\n'
        '    initialized = 1;\n'
        '  }\n'
        '  memcpy(model.U, U, sizeof(real_T) * (*I));\n'
        '  model.step();\n'
        '  Y[0] = model.Y[0];\n'
        '  *STATUS = 0;\n'
        '}\n'
    ], simulink_model_name, simulink_model_name);
    
    % 4. Compile to .dll (gcc or MSVC)
    %    > mex -c source.c -> link into shared library
    %    > Copy .dll to PowerFactory UserDLL directory
    %
    % 5. In PowerFactory: create External Model → digexfun → point to .dll
end
```

#### Path 3: FMU Export

```matlab
% Simulink → FMU (Functional Mock-up Unit)
% PowerFactory can import FMUs for co-simulation

% Configure FMU export
set_param(model_name, 'FMUType', 'CoSimulation');
set_param(model_name, 'FMUSourceCode', 'on');

% Export
fmuexport(model_name, 'output.fmu');

% PowerFactory: Insert → External Model → FMU → load .fmu
```

#### Path 4: MATLAB → Python → PowerFactory API

```matlab
% src/export_to_pf_python_api.m
function export_to_pf_python_api(mpc, models)
    % Use MATLAB's Python bridge to drive PowerFactory Python API
    
    % Start PowerFactory
    pf = py.powerfactory.GetApplication();
    prj = pf.CreateProject('translated_case');
    
    % Create network from MATPOWER data
    for i = 1:length(mpc.bus)
        bus = pf.CreateObject('ElmNet\\ElmTerm');
        bus.loc_name = sprintf('BUS_%d', mpc.bus(i, 1));
        bus.uknom = mpc.bus(i, 10) * 1e3;  % kV -> V
        % ... set other bus parameters ...
    end
    
    % Create dynamic models from registry
    for i = 1:length(models)
        model = models(i);
        mapping = registry.lookup(model.name);
        % ... create DSL instance, set parameters ...
    end
    
    % Run simulation
    pf.RunSimulation();
    
    % Export results
    pf.Export('results.csv');
end
```

## Implementation Steps

### Phase 1: MATLAB Parser + Simulink Verification Environment (2–3 weeks)

**Step 1:** Set up MATPOWER (free, open-source)
```
>> loadcase('case14')
>> mpc = psse2mpc('models/psse/ieee14.raw')
```
- Verify parsed bus/branch/generator data matches PSSE case
- Document any parsing limitations

**Step 2:** Write `.dyr` parser in MATLAB
```
>> models = parse_dyr('models/psse/ieee14.dyr')
```
- Returns struct array: bus, name, id, params[]
- Validate by cross-referencing known model parameter counts

**Step 3:** Build ModelRegistry class
- Map PSSE standard models → Simulink block parameters → PowerFactory DSL parameters
- Include correction factors (damping, saturation, step-up transformer)
- Support NEM-specific naming aliases

**Step 4:** Build Simulink from parsed models
- Programmatically generate .slx from model registry + parsed parameters
- One Simulink model per composite generator (gen + exciter + gov + PSS)
- Run same disturbance as PSSE → compare results
- **This is the TRUTH verification environment** — if Simulink and PSSE agree, the translation is correct at the block-diagram level

**Deliverable:** MATLAB scripts that:
- Parse IEEE 14-bus `.raw` + `.dyr`
- Build equivalent Simulink model
- Run 3-phase fault disturbance
- Compare Simulink vs PSSE output
- Generate comparison report

### Phase 2: Simulink → PowerFactor Export (2–3 weeks)

**Step 5:** DSL Code Generation (Export Path 1)
- Implement Simulink block → DSL line translator for all standard block types:
  - `TransferFcn` → DSL `inc(transfer_function)`
  - `Gain` → `kp(gain)`
  - `Saturation` → `lim(lower, upper)`
  - `Sum` → `sum(+)`, `sum(-)`, `sum(+-)`
  - `Integrator` → `integ(t_const)`
  - `PID Controller` → `pi(Kp, Ki)`
- Validate: hand-translate one model (ESST3A), compare to auto-generated DSL

**Step 6:** FMU Export (Export Path 3)
- Export a validated Simulink model as FMU
- Import into PowerFactory
- Run co-simulation → verify Dynamic response matches
- **This is the fastest path to a working PSSE→SIMULINK→PF bridge**

**Step 7:** Python API integration (Export Path 4)
- Create a MATLAB wrapper script that calls Python → PowerFactory API
- End-to-end: MATLAB parses → builds Simulink → validates → drives Python API → creates PF project → runs simulation → compares results

**Deliverable:** MATLAB pipeline that:
- Parses PSSE → Simulink → validates
- Exports to PowerFactory (via DSL, FMU, or Python API)
- Runs matching disturbance in both → produces comparison report

### Phase 3: System Identification for UDMs (3–5 weeks)

**Step 8:** Test signal generator
- Create MATLAB script that generates standard test signals for PSSE
- Step, ramp, chirp, PRBS at configurable magnitudes

**Step 9:** UDM identification workflow
- Run UDM in PSSE with test signals → save I/O time-series
- Load into System Identification Toolbox
- Identify transfer function structure
- Build equivalent Simulink model
- Validate against different test signals

**Step 10:** Identified model → PowerFactory
- Use same Export Path 1/2/3 for identified UDM
- For linear identified models: DSL generation (Path 1)
- For non-linear identified models: C code → DLL (Path 2)

**Deliverable:** MATLAB scripts that:
- Take a Fortran UDM (compiled .dll reference PSSE case)
- Run test signals, capture I/O
- Identify transfer function
- Build Simulink + export to PowerFactory
- Validate against original UDM in PSSE

### Phase 4: Automation & Reporting (1–2 weeks)

**Step 11:** Batch translation pipeline
- Process multiple cases with one command
- Parallel execution across cases
- Automated comparison reporting

**Step 12:** Validation dashboard
- MATLAB App Designer or web-based dashboard
- Side-by-side time-series comparison
- Metric summary (RMSE, max deviation, settling time)
- Parameter transformation log (for audit/traceability)

## Test Harness

```matlab
% tests/run_strategy_d_tests.m
% Strategy D: MATLAB/Simulink Translation Hub Verification

%% Test 1: MATPOWER .raw parsing
mpc = psse2mpc('../models/psse/ieee14.raw');
assert(length(mpc.bus) == 14, 'Expected 14 buses');
assert(length(mpc.gen) == 5,  'Expected 5 generators');
fprintf('[PASS] MATPOWER parsed IEEE 14-bus .raw successfully\n');

%% Test 2: .dyr parsing
models = parse_dyr('../models/psse/ieee14.dyr');
fprintf('  Parsed %d dynamic models\n', length(models));
model_names = {models.name};
assert(any(strcmp(model_names, 'GENROU')), 'Missing GENROU');
assert(any(strcmp(model_names, 'ESST3A')), 'Missing ESST3A');
fprintf('[PASS] .dyr parser extracted all dynamic models\n');

%% Test 3: Model Registry completeness
reg = ModelRegistry();
for i = 1:length(models)
    mapping = reg.lookup(models(i).name);
    assert(~isempty(mapping), 'Missing registry entry for %s', models(i).name);
end
fprintf('[PASS] Model registry covers all models in .dyr\n');

%% Test 4: Simulink model generation
build_simulink_model(models, 'ieee14_translated');
assert(exist('ieee14_translated.slx', 'file') == 4);
fprintf('[PASS] Simulink model generated successfully\n');

%% Test 5: Simulink simulation runs
load_system('ieee14_translated');
simOut = sim('ieee14_translated', 'StopTime', '10');
assert(~isempty(simOut.logsout), 'Simulation produced no logged signals');
fprintf('[PASS] Simulink simulation completed\n');

%% Test 6: DSL code generation
dsl_code = export_to_pf_dsl('ieee14_translated/ESST3A_1');
assert(contains(dsl_code, 'class ESST3A'), 'Missing class declaration');
assert(contains(dsl_code, 'input'), 'Missing input declaration');
fprintf('[PASS] DSL code generated from Simulink model\n');

%% Test 7: Parameter mapping accuracy
% For a specific model, verify mapped parameters match known values
reg = ModelRegistry();
mapping = reg.lookup('GENROU');
expected_Tpdo = 7.4;  % from IEEE 14-bus .dyr
actual_Tpdo = mapping.apply('Tpdo', 7.4);
assert(abs(actual_Tpdo - expected_Tpdo) < 0.01);
fprintf('[PASS] Parameter mapping preserves expected values\n');

%% Test 8: System ID on known transfer function (simulated UDM)
% Generate test data from a known transfer function
sys_true = tf([1, 10], [1, 2, 5]);  % 2nd order
[~, t] = gensig('step', 5, 10, 0.01);
y = lsim(sys_true, t, t);
data = iddata(y, t, 0.01);
sys_id = tfest(data, 2, 1);
% Check identified TF matches true TF
[mag_true, phase_true] = bode(sys_true, 1:0.1:10);
[mag_id, phase_id] = bode(sys_id, 1:0.1:10);
fit = 100 * (1 - norm(mag_true - mag_id) / norm(mag_true - mean(mag_true)));
assert(fit > 85, 'System ID fit < 85%%: %.1f%%', fit);
fprintf('[PASS] System identification achieves %.1f%% fit\n', fit);
```

## Key MATLAB Toolbox Requirements

| Toolbox | Purpose | Need Level | Alternative |
|---------|---------|-----------|-------------|
| MATLAB Base | Core environment | Mandatory | — |
| Simulink | Block diagram modeling | Mandatory | — |
| MATPOWER | PSSE .raw parsing | Mandatory | Free, open-source |
| Control System Toolbox | Transfer function analysis | High | — |
| System Identification Toolbox | UDM reverse-engineering | High | Free alternative: sysidentpy (Python) |
| Simulink Coder | C code generation for DLL | Medium | FMU export without source |
| Simscape Electrical | Power system component library | Medium | Standard Simulink blocks |
| Embedded Coder | Optimized C code for DLL | Medium | Simulink Coder sufficient |
| Parallel Computing Toolbox | Batch translation | Low | Sequential processing OK |
| MATLAB Compiler | Deploy as standalone | Low | Not needed for in-house |

## Advantages Over Strategies A–C

| Aspect | Strategy D Advantage |
|--------|---------------------|
| **UDM handling** | **Unique capability**: System ID reverse-engineers UDMs without source code. No other strategy can do this. |
| **Verification** | Simulink is an independent simulation engine — you verify the translation BEFORE reaching PowerFactory. If Simulink and PSSE agree, the PowerFactory version will too. |
| **Block-diagram fidelity** | Both PSSE and Simulink use the same visual block diagram paradigm. Translation is one-to-one at the structural level, not parameter re-mapping. |
| **MATPOWER ecosystem** | MATPOWER already parses .raw completely. No dependency on ANDES or pandapower. |
| **FMU standard** | FMU/FMI is the ISO standard for model exchange. PowerFactory supports it. This is future-proof. |
| **DLL pathway for complex models** | If DSL can't express it, C code from Simulink Coder can. PowerFactory's digexfun accepts external DLLs. |
| **Co-simulation** | PowerFactory digexfun → MATLAB engine mode enables timestep-by-timestep comparison during development. |
| **MATLAB scripting power** | Numerical analysis, optimization, plotting, reporting — all in one environment. No tool-switching. |

## Limitations

1. **MATLAB license cost** — MATLAB + Simulink + required toolboxes are commercial. MATPOWER is free but the rest needs a license.
2. **Simulink Coder DLL pathway** — Compiling .dlls requires a C compiler toolchain and PowerFactory digexfun configuration. Some IT environments restrict this.
3. **No turnkey solution** — This is a framework, not a product. You build the pipeline from available parts.
4. **System Identification accuracy** — For highly non-linear UDMs (look-up tables, state machines, hysteresis), the identified model may not capture all behaviours with a single transfer function.
5. **Model Registry setup effort** — First-time mapping for each model type is manual work, similar to Strategy B.
6. **MATLAB-Python interop quirks** — The `py.` namespace has type conversion issues with complex nested structs.

## When to Choose This Strategy

- **Best for**: Organisations that already have MATLAB/Simulink licenses (universities, AEMO, many utilities)
- **Best for**: Solving the UDM problem (Fortran models without source code)
- **Best for**: Teams that want an independent verification environment before committing to PowerFactory
- **Best for**: Research projects where you need maximum flexibility in model manipulation
- **Less ideal for**: Production pipelines where PowerFactory is the only destination and all models are standard library

## Recommended Integration with Other Strategies

**Strategy D + A**: Use Strategy A's native import as the baseline, Strategy D's Simulink as the verification tool. Run the same disturbance in both Simulink (from parsed PSSE) and PowerFactory (from native import). If they differ, the issue is PowerFactory's import, not the model data.

**Strategy D + B**: Strategy B's model registry YAML format → convert to MATLAB class for Dual use. Strategy D's System ID replaces Strategy B's aspirational Fortran parser for UDMs.

**Strategy D + C**: Generate CIM XML from MATLAB directly (MATLAB has XML tools). This gives a clean PSSE→MATLAB→CIM→PF path without Strategy C's PSSE→CIM converter problem.

## Estimated Effort

| Phase | Scope | Duration |
|-------|-------|----------|
| **1** | MATLAB parser + Simulink verification | 2–3 weeks |
| **2** | Export paths (DSL, FMU, Python API) | 2–3 weeks |
| **3** | System Identification for UDMs | 3–5 weeks |
| **4** | Automation, batch processing, dashboard | 1–2 weeks |
| **Total** | Full pipeline | **8–13 weeks** |

**Fast-track option** (Phase 1 only, 2–3 weeks): Get a Simulink verification environment that proves block-diagram equivalence. This alone is valuable as a cross-check against Strategies A–C results, without building the PowerFactory export pipeline.

## References

1. **MATPOWER PSSE parser**: https://matpower.org/docs/ref/matpower5.0/psse_parse.html
2. **Simulink Coder**: https://au.mathworks.com/products/simulink-coder.html
3. **Embedded Coder**: https://au.mathworks.com/products/embedded-coder.html
4. **System Identification Toolbox**: https://au.mathworks.com/products/sysid.html
5. **Simscape Electrical**: https://au.mathworks.com/products/simscape-electrical.html
6. **FMU Export from Simulink**: https://au.mathworks.com/help/fmuexport/
7. **MATLAB-PowerFactory integration (MATLAB Central)**: https://au.mathworks.com/matlabcentral/answers/1978384
8. **Co-simulation PowerFactory-MATLAB (DTU)**: https://orbit.dtu.dk/en/publications/co-simulation-with-digsilent-powerfactory-and-matlab-optimal-inte/
9. **PowerFactory-Tools Python API**: https://medium.com/@Sebastian-DD/automate-powerfactory-with-python-and-powerfactory-tools-e96d33adda74
10. **digexfun interface (DIgSILENT)**: https://www.digsilent.de/en/scripting-and-automation.html
11. **FMI Standard**: https://fmi-standard.org/
12. **Karlsson (2013) — PSSE vs PowerFactory comparison**: https://www.diva-portal.org/smash/get/diva2:658793/FULLTEXT01.pdf
