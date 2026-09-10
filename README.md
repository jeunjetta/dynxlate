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
├── plans/           # Research, links, and implementation strategies
├── src/             # Translation code
├── tests/           # Test harnesses
├── models/          # Example models (IEEE, WECC, generic)
│   ├── psse/       # .raw + .dyr files
│   ├── pscad/      # PSCAD case files
│   └── powerfactory/ # Translated .pfd / DSL / DPL
└── results/         # Simulation comparison outputs
```

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
