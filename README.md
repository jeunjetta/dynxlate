# Dynxlate

Dynamic model translation between power systems simulation formats.

**Source formats:** PSSE (`.raw` + `.dyr`, block diagram & Fortran), PSCAD, SSAT
**Target format:** PowerFactory (`.pfd` / DPL / DSL)

## Goal

Translate transient dynamic models (generators, SVCs, inverters, etc.) from PSSE/PSCAD/SSAT into PowerFactory format, then verify by running the same snapshot + disturbance through both engines and comparing results.

## Video Explainer

Watch this short video for a quick overview of the ideal end state of phase 1 (still WIP though!).
/assets/Automating_Grid_Model_Translation__The_Architecture_of_Dynxlate.mp4

## Slidepack

/assets/Dynxlate_Dynamic_Model_Translation.pdf or pptx

## Project Structure

```
dynxlate/
├── plans/           	# Research, links, and implementation strategies
│       research.md
│       critique.md
│       emt-ibr-context.md
│       strategy-a-native-import.md
│       strategy-b-andes-dsl-generator.md
│       strategy-c-cim-intermediate.md
│       strategy-d-matlab-simulink-translator.md
├── src/             	# Translation code
│   └───dynaxlate
│           comparison.py
│           dsl_generator.py
│           dyr_parser.py
│           fortran_parser.py
│           model_registry.py
│           pf_adapter.py
│           psse_baseline.py
│           __init__.py
├── tests/           	# UDM, validation and strategy test suites
├───assets
│       Automating_Grid_Model_Translation__The_Architecture_of_Dynxlate.mp4
│       Dynxlate_Dynamic_Model_Translation.pdf
│       Dynxlate_Dynamic_Model_Translation.pptx
│       Dynxlate_Folder_Snapshot.png
│       Pandapower_for_Modeling_Analysis_and_Optimization_of_Electric_Power_Systems.pdf
├───graphify-out		# architecture analysis and code graphs
├── models/          	# Example models (IEEE, WECC, generic)
│   ├── psse/       	# .raw + .dyr files
│   ├── fortran/      	# usrexc.f, usrgov.f, usrpss.f
│   └── powerfactory/ 	# Translated .pfd / DSL / DPL
└── results/         	# Simulation comparison outputs
```

"dynxlate/assets/dynxlate_folder_snapshot.png"

---

## Understanding this codebase (graphify)

This repo has a persistent knowledge graph at `graphify-out/` — an AST + LLM-extracted map of
files, functions, communities, and cross-file relationships, with an interactive HTML view,
GraphRAG-ready JSON, and a plain-language `GRAPH_REPORT.md` audit report.

**For humans:** open `graphify-out/graph.html` in a browser to explore visually, or read
`graphify-out/GRAPH_REPORT.md` for the architecture summary (god nodes, communities, surprising
connections).

**For AI agents:** install the graphify skill for your harness, then just ask questions about the
codebase — the graph is checked automatically before falling back to raw file exploration.

```bash
# Install the graphify CLI + skill (one-time, per machine)
uv tool install graphifyy
graphify install --platform claude   # or: codex, droid, gemini, cursor, hermes, aider, ...

# Query this repo's graph directly
graphify query "<question>" .
graphify path "<A>" "<B>" .
graphify explain "<concept>" .

# Keep it current after code changes
graphify update .          # AST-only, free, fast
graphify extract . --backend gemini --force   # full re-extraction incl. semantic/LLM pass
```

Project homepage: https://github.com/Graphify-Labs/graphify · https://graphify.net

## Python package layout

The checkout is `/home/kar/dev/dynxlate` and the installable package lives in
`src/dynxlate/`. Keep this package directory: modules use relative imports and
the wheel exposes the `dynxlate` namespace. Run `uv sync --locked` after moving
a checkout. Python callers should use `from dynxlate...`, replacing the former
`dynaxlate` import name.
