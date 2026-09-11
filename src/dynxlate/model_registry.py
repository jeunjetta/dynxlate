"""
Model Registry: PSSE ↔ PowerFactory parameter mapping.

YAML-driven mapping tables for standard PSSE dynamic models
to their PowerFactory DSL equivalents.
"""

from pathlib import Path
from dataclasses import dataclass, field
import yaml


@dataclass
class ParameterMapping:
    """Single parameter mapping from PSSE to PowerFactory."""
    psse_name: str
    pf_name: str
    scale: float = 1.0
    offset: float = 0.0
    unit_psse: str = ""
    unit_pf: str = ""
    notes: str = ""
    conditional: str | None = None  # Python expression for conditional mapping


@dataclass
class ModelMapping:
    """Complete model mapping from PSSE to PowerFactory."""
    psse_model: str
    pf_model_class: str          # e.g., "ElmSym", "ElmDsl"
    pf_template: str | None      # DSL template name in PF library
    category: str                # "generator", "exciter", "governor", "pss", "renewable"
    sim_domain: str = "rms"      # "rms", "emt", or "both" — see plans/emt-ibr-context.md
    parameters: list[ParameterMapping] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)

    def apply(self, psse_values: dict[str, float]) -> dict[str, float]:
        """Transform PSSE parameter values to PowerFactory values."""
        pf_values = {}
        for pm in self.parameters:
            if pm.psse_name in psse_values:
                val = psse_values[pm.psse_name]
                pf_values[pm.pf_name] = val * pm.scale + pm.offset
        return pf_values


# Built-in model registry for the most common PSSE models
BUILTIN_REGISTRY: dict[str, ModelMapping] = {}


def _load_builtin_registry():
    """Load built-in model mappings."""
    # GENROU: Round rotor generator model
    BUILTIN_REGISTRY["GENROU"] = ModelMapping(
        psse_model="GENROU",
        pf_model_class="ElmSym",
        pf_template="GENROU",
        category="generator",
        parameters=[
            ParameterMapping("H", "H",     scale=1.0, notes="Inertia constant (s)"),
            ParameterMapping("D", "D",      scale=1.0, notes="Damping — NOTE: different meaning in PF (rotor friction vs load-freq damping)"),
            ParameterMapping("Xd", "xd",    scale=1.0, notes="d-axis synchronous reactance"),
            ParameterMapping("Xq", "xq",    scale=1.0, notes="q-axis synchronous reactance"),
            ParameterMapping("Xdp", "xd_p", scale=1.0, notes="d-axis transient reactance"),
            ParameterMapping("Xqp", "xq_p", scale=1.0, notes="q-axis transient reactance"),
            ParameterMapping("Xdpp", "xd_pp", scale=1.0, notes="d-axis subtransient reactance"),
            ParameterMapping("Xqpp", "xq_pp", scale=1.0, notes="q-axis subtransient — PSSE assumes Xqpp=Xdpp, PF allows difference"),
            ParameterMapping("Tdp0", "td_p", scale=1.0, notes="d-axis open-circuit transient time constant (s)"),
            ParameterMapping("Tqp0", "tq_p", scale=1.0, notes="q-axis open-circuit transient time constant (s)"),
            ParameterMapping("Tdpp0", "td_pp", scale=1.0, notes="d-axis open-circuit subtransient time constant (s)"),
            ParameterMapping("Tqpp0", "tq_pp", scale=1.0, notes="q-axis open-circuit subtransient time constant (s)"),
            ParameterMapping("Xl", "xl",    scale=1.0, notes="Leakage reactance"),
            ParameterMapping("Ra", "ra",    scale=1.0, notes="Stator resistance — PF models explicitly, PSSE doesn't always"),
            ParameterMapping("S10", "S10",  scale=1.0, notes="Saturation factor at 1.0 pu"),
            ParameterMapping("S12", "S12",  scale=1.0, notes="Saturation factor at 1.2 pu"),
        ],
        corrections=[
            "Saturation model differs: PSSE affects mutual+leakage, PF affects mutual only",
            "Damping constant NOT imported by PF native import — must set manually",
            "PSSE assumes Xdpp=Xqpp; PF allows difference — set Xqpp=Xdpp for equivalence",
        ],
        known_issues=[
            "Step-up transformer handling depends on PSSE generator data",
            "Operational impedance vs coupled circuit model differences",
        ]
    )

    # ESST3A: Static exciter type 3A
    BUILTIN_REGISTRY["ESST3A"] = ModelMapping(
        psse_model="ESST3A",
        pf_model_class="ElmDsl",
        pf_template="ESST3A",
        category="exciter",
        parameters=[
            ParameterMapping("TR", "TR", scale=1.0, notes="Sensor time constant (s)"),
            ParameterMapping("VMAX", "VMAX", scale=1.0, notes="Max output voltage"),
            ParameterMapping("VMIN", "VMIN", scale=1.0, notes="Min output voltage"),
            ParameterMapping("VAMAX", "VAMAX", scale=1.0, notes="Max regulator output"),
            ParameterMapping("VAMIN", "VAMIN", scale=1.0, notes="Min regulator output"),
            ParameterMapping("KC", "KC", scale=1.0, notes="Rectifier loading factor"),
        ],
        corrections=[
            "Check voltage measurement point matches generator terminal",
        ],
    )

    # EXDC2: DC exciter type 2
    BUILTIN_REGISTRY["EXDC2"] = ModelMapping(
        psse_model="EXDC2",
        pf_model_class="ElmDsl",
        pf_template="EXDC2",
        category="exciter",
        parameters=[
            ParameterMapping("TR", "TR", scale=1.0, notes="Sensor time constant (s)"),
            ParameterMapping("KA", "KA", scale=1.0, notes="Regulator gain"),
            ParameterMapping("TA", "TA", scale=1.0, notes="Regulator time constant (s)"),
            ParameterMapping("VRMAX", "VRMAX", scale=1.0, notes="Max regulator output"),
            ParameterMapping("VRMIN", "VRMIN", scale=1.0, notes="Min regulator output"),
        ],
    )

    # TGOV1: Turbine governor type 1
    BUILTIN_REGISTRY["TGOV1"] = ModelMapping(
        psse_model="TGOV1",
        pf_model_class="ElmDsl",
        pf_template="TGOV1",
        category="governor",
        parameters=[
            ParameterMapping("R", "R", scale=1.0, notes="Governor droop"),
            ParameterMapping("T1", "T1", scale=1.0, notes="Steam chest time constant (s)"),
            ParameterMapping("T2", "T2", scale=1.0, notes="Reheater time constant (s)"),
            ParameterMapping("T3", "T3", scale=1.0, notes="Crossover time constant (s)"),
            ParameterMapping("VMAX", "VMAX", scale=1.0, notes="Max valve position"),
            ParameterMapping("VMIN", "VMIN", scale=1.0, notes="Min valve position"),
        ],
    )

    # IEEEG1: IEEE governor type 1
    BUILTIN_REGISTRY["IEEEG1"] = ModelMapping(
        psse_model="IEEEG1",
        pf_model_class="ElmDsl",
        pf_template="IEEEG1",
        category="governor",
        parameters=[
            ParameterMapping("K", "K", scale=1.0, notes="Governor gain"),
            ParameterMapping("T1", "T1", scale=1.0, notes="Time constant 1 (s)"),
            ParameterMapping("T2", "T2", scale=1.0, notes="Time constant 2 (s)"),
            ParameterMapping("T3", "T3", scale=1.0, notes="Time constant 3 (s)"),
        ],
    )

    # IEEEST: IEEE power system stabilizer
    BUILTIN_REGISTRY["IEEEST"] = ModelMapping(
        psse_model="IEEEST",
        pf_model_class="ElmDsl",
        pf_template="IEEEST",
        category="pss",
        parameters=[
            ParameterMapping("MODE", "MODE", scale=1.0, notes="Input signal mode"),
            ParameterMapping("KSS", "KSS", scale=1.0, notes="PSS gain"),
        ],
        corrections=[
            "Input signal selection must match between PSSE and PF",
        ],
    )

    # ST2CUT: Double-input stabilizer
    BUILTIN_REGISTRY["ST2CUT"] = ModelMapping(
        psse_model="ST2CUT",
        pf_model_class="ElmDsl",
        pf_template="ST2CUT",
        category="pss",
    )

    # EXST1: Static exciter type 1
    BUILTIN_REGISTRY["EXST1"] = ModelMapping(
        psse_model="EXST1",
        pf_model_class="ElmDsl",
        pf_template="EXST1",
        category="exciter",
    )

    # GENCLS: Classical generator model
    BUILTIN_REGISTRY["GENCLS"] = ModelMapping(
        psse_model="GENCLS",
        pf_model_class="ElmSym",
        pf_template="GENCLS",
        category="generator",
        sim_domain="rms",
        parameters=[
            ParameterMapping("H", "H", scale=1.0, notes="Inertia constant (s)"),
            ParameterMapping("D", "D", scale=1.0, notes="Damping coefficient"),
        ],
        corrections=[
            "Simplest model: only H and D — good for initial testing",
        ],
    )

    # === IBR Models (sim_domain: emt) ===
    # These models NEED EMT simulation for fidelity in weak grids.
    # See plans/emt-ibr-context.md for justification.

    # REGC_A: Renewable energy generator/converter model A
    BUILTIN_REGISTRY["REGC_A"] = ModelMapping(
        psse_model="REGC_A",
        pf_model_class="ElmDsl",
        pf_template="REGC_A",
        category="renewable",
        sim_domain="emt",
        parameters=[
            ParameterMapping("Tg", "Tg", scale=1.0, notes="Converter time constant (s)"),
            ParameterMapping("Rrpu", "Rrpu", scale=1.0, notes="Low voltage power logic"),
            ParameterMapping("Iqmax", "Iqmax", scale=1.0, notes="Max q-axis current (pu)"),
            ParameterMapping("Iqmin", "Iqmin", scale=1.0, notes="Min q-axis current (pu)"),
            ParameterMapping("Vdip", "Vdip", scale=1.0, notes="Voltage dip threshold"),
            ParameterMapping("Vup", "Vup", scale=1.0, notes="Voltage up threshold"),
        ],
        corrections=[
            "PLL dynamics in weak grids require EMT resolution",
            "Current limiting behavior differs between RMS and EMT",
            "At SCR < 3, RMS results diverge significantly from EMT",
        ],
        known_issues=[
            "PPC interactions with nearby controllers can't be captured in RMS",
            "Ride-through behavior during voltage dips needs EMT validation",
        ],
    )

    # REEC_B: Renewable energy electrical control model B
    BUILTIN_REGISTRY["REEC_B"] = ModelMapping(
        psse_model="REEC_B",
        pf_model_class="ElmDsl",
        pf_template="REEC_B",
        category="renewable",
        sim_domain="emt",
        parameters=[
            ParameterMapping("Vdip", "Vdip", scale=1.0, notes="Voltage dip threshold"),
            ParameterMapping("Vup", "Vup", scale=1.0, notes="Voltage up threshold"),
            ParameterMapping("Trv", "Trv", scale=1.0, notes="Voltage sensor time constant (s)"),
            ParameterMapping("Kqv", "Kqv", scale=1.0, notes="Q/_voltage gain"),
        ],
        corrections=[
            "Active current management during faults needs EMT verification",
            "Reactive power priority vs active power priority is EMT-dependent",
        ],
    )

    # REPC_A: Renewable energy plant control model A
    BUILTIN_REGISTRY["REPC_A"] = ModelMapping(
        psse_model="REPC_A",
        pf_model_class="ElmDsl",
        pf_template="REPC_A",
        category="renewable",
        sim_domain="both",
        parameters=[
            ParameterMapping("Tfltr", "Tfltr", scale=1.0, notes="Voltage filter time constant (s)"),
            ParameterMapping("Kp", "Kp", scale=1.0, notes="Proportional gain"),
            ParameterMapping("Ki", "Ki", scale=1.0, notes="Integral gain"),
        ],
        corrections=[
            "PPC interactions are the #1 cause of IBR oscillations (Dominion case)",
            "RMS mode OK for steady-state; EMT mode needed for interaction analysis",
        ],
        known_issues=[
            "Multiple REPC_A models in close proximity can interact",
            "Tuning without considering nearby controllers causes oscillations",
        ],
    )


_load_builtin_registry()


def load_registry(yaml_path: str | Path) -> dict[str, ModelMapping]:
    """Load model registry from a YAML file.

    YAML format per model:
        psse_model: GENROU
        pf_model_class: ElmSym
        pf_template: GENROU
        category: generator
        parameters:
          - psse_name: H
            pf_name: H
            scale: 1.0
            notes: Inertia constant
        corrections:
          - "Damping not imported"
        known_issues:
          - "Saturation model differs"
    """
    registry = {}
    path = Path(yaml_path)
    if path.is_file():
        with open(path) as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            for model_data in data:
                mapping = ModelMapping(
                    psse_model=model_data["psse_model"],
                    pf_model_class=model_data["pf_model_class"],
                    pf_template=model_data.get("pf_template"),
                    category=model_data["category"],
                    parameters=[
                        ParameterMapping(**p) for p in model_data.get("parameters", [])
                    ],
                    corrections=model_data.get("corrections", []),
                    known_issues=model_data.get("known_issues", []),
                )
                registry[mapping.psse_model] = mapping
    return registry


def get_mapping(psse_model_name: str) -> ModelMapping | None:
    """Look up a model mapping by PSSE model name."""
    return BUILTIN_REGISTRY.get(psse_model_name.upper().strip())


def list_supported_models() -> list[str]:
    """List all PSSE model names in the registry."""
    return sorted(BUILTIN_REGISTRY.keys())
