"""
DSL Generator: emit PowerFactory DSL model definitions from parsed Fortran UDMs.

Translation rules (Tier 2 path per plans/critique.md):
  - CON(J+n)        -> DSL parameter (named from header comments)
  - STATE(K+n)      -> DSL state variable
  - DSTATE(K+n) = e -> DSL state equation:  x. = e
  - VAR(L+n)        -> internal signal (inter-mode storage)
  - MODE 1 block    -> inc() initial conditions
  - MODE 3 block    -> output equations
  - PSSE machine quantities -> DSL input/output signals (see SIGNAL_MAP)
  - AMIN1/AMAX1     -> min()/max(); ABS -> abs; ** stays **

Anything the Fortran parser flagged as unsupported is carried into the
generated DSL as a `! TODO(manual)` comment so a human finishes the job —
the generator never silently drops behaviour.
"""

from dataclasses import dataclass, field
import re

from .fortran_parser import FortranUDM

# PSSE machine-array quantities -> DSL signal name.
# Direction is decided by usage: assigned (LHS) => output, read (RHS) => input.
SIGNAL_MAP = {
    "ETERM":  "u",       # terminal voltage magnitude
    "SPEED":  "speed",   # rotor speed deviation
    "VREF":   "vref",    # voltage reference
    "VOTHSG": "upss",    # stabilizer signal (PSS writes it, exciter reads it)
    "PMECH":  "pt",      # mechanical power
    "EFD":    "ve",      # field voltage
    "ANGLE":  "phi",
    "PELEC":  "pgt",
    "QELEC":  "qgt",
}

_FORTRAN_FUNCS = [
    (re.compile(r"\bAMIN1\b", re.IGNORECASE), "min"),
    (re.compile(r"\bAMAX1\b", re.IGNORECASE), "max"),
    (re.compile(r"\bABS\b", re.IGNORECASE), "abs"),
    (re.compile(r"\bSQRT\b", re.IGNORECASE), "sqrt"),
    (re.compile(r"\bEXP\b", re.IGNORECASE), "exp"),
]


@dataclass
class DSLModel:
    """Generated PowerFactory DSL model."""
    name: str
    source: str
    parameters: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)

    @property
    def needs_manual_review(self) -> bool:
        return bool(self.todos)


class DSLGenerator:
    """Generate PowerFactory DSL source from a parsed Fortran UDM."""

    def __init__(self, udm: FortranUDM):
        self.udm = udm
        self.inputs: set[str] = set()
        self.outputs: set[str] = set()

    # ── expression translation ────────────────────────────────────────

    def _subst_arrays(self, expr: str) -> str:
        """Replace CON/STATE/DSTATE/VAR array refs with declared names."""
        def repl(m: re.Match) -> str:
            kind = m.group(1).upper()
            off = int(m.group(2) or 0)
            if kind == "CON":
                return self.udm.con_name(off)
            if kind in ("STATE", "DSTATE"):
                return self.udm.state_name(off)
            if kind == "VAR":
                return self.udm.var_name(off)
            return f"ICON{off}"
        return re.sub(
            r"(CON|DSTATE|STATE|VAR|ICON)\(\s*[JKLM]\s*(?:\+\s*(\d+))?\s*\)",
            repl, expr, flags=re.IGNORECASE)

    def _subst_signals(self, expr: str, is_lhs: bool = False) -> str:
        """Replace PSSE machine quantities QUANT(MC) with DSL signal names."""
        def repl(m: re.Match) -> str:
            quant = m.group(1).upper()
            if quant in SIGNAL_MAP:
                name = SIGNAL_MAP[quant]
                (self.outputs if is_lhs else self.inputs).add(name)
                return name
            return m.group(0)
        return re.sub(r"(\w+)\(\s*MC\s*\)", repl, expr, flags=re.IGNORECASE)

    def _subst_funcs(self, expr: str) -> str:
        for pat, dsl in _FORTRAN_FUNCS:
            expr = pat.sub(dsl, expr)
        return expr

    def translate_expr(self, expr: str, is_lhs: bool = False) -> str:
        expr = self._subst_arrays(expr)
        expr = self._subst_signals(expr, is_lhs=is_lhs)
        expr = self._subst_funcs(expr)
        return re.sub(r"\s+", " ", expr).strip()

    def _translate_limiter(self, stmt: str) -> tuple[str, str] | None:
        """Fortran logical-IF limiter -> min/max.

        IF (X .GT. LIM) X = LIM   ->   x = min(x, lim)
        IF (X .LT. LIM) X = LIM   ->   x = max(x, lim)
        Handles nested parens (CON(J+3) etc.) via balanced-paren scan.
        """
        s = stmt.strip()
        if not re.match(r"IF\s*\(", s, re.IGNORECASE):
            return None
        start = s.index("(")
        depth, end = 0, -1
        for i in range(start, len(s)):
            if s[i] == "(":
                depth += 1
            elif s[i] == ")":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end < 0:
            return None
        cond, rest = s[start + 1:end], s[end + 1:].strip()
        m = re.match(r"(.+?)\s*\.(GT|LT)\.\s*(.+)$", cond, re.IGNORECASE)
        if not m or "=" not in rest:
            return None
        cond_var, op, limit = m.group(1).strip(), m.group(2).upper(), m.group(3).strip()
        lhs, rhs = (p.strip() for p in rest.split("=", 1))
        if cond_var.upper() != lhs.upper() or limit.upper() != rhs.upper():
            return None  # not a self-limiter; caller flags for manual review
        fn = "min" if op == "GT" else "max"
        lhs_t = self.translate_expr(lhs, is_lhs=True)
        return lhs_t, f"{fn}({self.translate_expr(cond_var)}, {self.translate_expr(limit)})"

    def _translate_stmt(self, stmt: str) -> tuple[str, str] | None:
        """Return (lhs, rhs) in DSL form, or None if not translatable."""
        limiter = self._translate_limiter(stmt)
        if limiter:
            return limiter
        if re.match(r"IF\s*\(", stmt.strip(), re.IGNORECASE):
            return None  # conditional we can't reduce — caller flags it

        if "=" not in stmt:
            return None
        lhs, rhs = stmt.split("=", 1)
        lhs, rhs = lhs.strip(), rhs.strip()
        is_deriv = bool(re.match(r"DSTATE\s*\(", lhs, re.IGNORECASE))
        lhs_t = self.translate_expr(lhs, is_lhs=True)
        rhs_t = self.translate_expr(rhs)
        if is_deriv:
            lhs_t += "."
        return lhs_t, rhs_t

    # ── generation ────────────────────────────────────────────────────

    def generate(self, model_name: str | None = None) -> DSLModel:
        udm = self.udm
        name = model_name or udm.subroutine or udm.path.stem.upper()

        init_eqs, deriv_eqs, output_eqs = [], [], []
        untranslated: list[str] = []
        for mode, target in ((1, init_eqs), (2, deriv_eqs), (3, output_eqs)):
            for stmt in udm.mode_blocks.get(mode, []):
                t = self._translate_stmt(stmt)
                if t:
                    target.append(f"{t[0]} = {t[1]}")
                else:
                    untranslated.append(f"untranslated MODE {mode} statement: `{stmt}`")

        params = [d.name for d in udm.cons]
        states = [d.name for d in udm.states]
        internals = [d.name for d in udm.vars]

        lines = [
            f"! DSL model {name} — auto-generated by dynaxlate from {udm.path.name}",
            "! Review before use: verify per-unit bases, limits, and initial conditions.",
            f"model {name}",
        ]

        # Equations first so input/output sets are populated.
        body: list[str] = []
        if states:
            body.append("  ! state variables: " + ", ".join(s.lower() for s in states))
        if internals:
            body.append("  ! internal signals: " + ", ".join(s.lower() for s in internals))
        if init_eqs:
            body.append("  ! initial conditions (from MODE 1)")
            body += [f"  inc({_lc(e)})" for e in init_eqs]
        if deriv_eqs:
            body.append("  ! state equations (from MODE 2)")
            body += [f"  {_lc(e)}" for e in deriv_eqs]
        if output_eqs:
            body.append("  ! output equations (from MODE 3)")
            body += [f"  {_lc(e)}" for e in output_eqs]

        todos = list(udm.warnings) + untranslated
        for w in todos:
            body.append(f"  ! TODO(manual): {w}")

        inputs = sorted(self.inputs - self.outputs)  # init reads of outputs aren't inputs
        outputs = sorted(self.outputs)
        header = []
        if inputs:
            header.append("  input " + ", ".join(inputs))
        if outputs:
            header.append("  output " + ", ".join(outputs))
        if params:
            header.append("  parameter " + ", ".join(p.lower() for p in params))

        lines += header + body + ["end"]

        return DSLModel(
            name=name,
            source="\n".join(lines) + "\n",
            parameters=[p.lower() for p in params],
            states=[s.lower() for s in states],
            inputs=inputs,
            outputs=outputs,
            todos=todos,
        )


def _lc(equation: str) -> str:
    """Lowercase identifiers (DSL convention) but keep function names intact."""
    return equation.lower()


def translate_udm(path, model_name: str | None = None) -> DSLModel:
    """Convenience: parse a Fortran UDM file and generate its DSL model."""
    from .fortran_parser import parse_fortran_udm
    udm = parse_fortran_udm(path)
    return DSLGenerator(udm).generate(model_name)
