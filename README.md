# Dynaxlate

Dynamic model translation between power systems simulation formats.

**Source formats:** PSSE (`.raw` + `.dyr`, block diagram & Fortran), PSCAD, SSAT
**Target format:** PowerFactory (`.pfd` / DPL / DSL)

## Goal

Translate transient dynamic models (generators, SVCs, inverters, etc.) from PSSE/PSCAD/SSAT into PowerFactory format, then verify by running the same snapshot + disturbance through both engines and comparing results.

## Project Structure

```
dynaxlate/
├── plans/           # Research, links, and implementation strategies
├── src/             # Translation code
├── tests/           # Test harnesses
├── models/          # Example models (IEEE, WECC, generic)
│   ├── psse/       # .raw + .dyr files
│   ├── pscad/      # PSCAD case files
│   └── powerfactory/ # Translated .pfd / DSL / DPL
└── results/         # Simulation comparison outputs
```
