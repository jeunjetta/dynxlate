"""
Fortran UDM Parser: extract structure from PSSE user-defined model source.

PSSE UDMs follow a rigid convention (see PSSE POM ch. "Writing User Models"):
  - Header comments declare CON/STATE/VAR/ICON allocations with names
  - One subroutine with MODE-dispatched blocks:
      MODE 1 = initialization, MODE 2 = state derivatives, MODE 3 = outputs
  - Array refs: CON(J+n), STATE(K+n), DSTATE(K+n), VAR(L+n), ICON(M+n)

This parser targets that convention. It is NOT a general Fortran frontend —
constructs outside the supported subset (DO loops, GOTO, DATA tables,
local arrays) are collected as warnings for manual translation (Tier 2
per plans/critique.md UDM tiers).
"""

from pathlib import Path
from dataclasses import dataclass, field
import re


@dataclass
class Declaration:
    """One CON/STATE/VAR/ICON allocation declared in the header comments."""
    kind: str          # "CON", "STATE", "VAR", "ICON"
    offset: int        # 0 for CON(J), 1 for CON(J+1), ...
    name: str          # e.g. "TR"
    unit: str = ""
    description: str = ""


@dataclass
class FortranUDM:
    """Parsed PSSE Fortran user-defined model."""
    path: Path
    subroutine: str = ""
    cons: list[Declaration] = field(default_factory=list)
    states: list[Declaration] = field(default_factory=list)
    vars: list[Declaration] = field(default_factory=list)
    icons: list[Declaration] = field(default_factory=list)
    mode_blocks: dict[int, list[str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def con_name(self, offset: int) -> str:
        for d in self.cons:
            if d.offset == offset:
                return d.name
        return f"CON{offset}"

    def state_name(self, offset: int) -> str:
        for d in self.states:
            if d.offset == offset:
                return d.name
        return f"STATE{offset}"

    def var_name(self, offset: int) -> str:
        for d in self.vars:
            if d.offset == offset:
                return d.name
        return f"VAR{offset}"


# Header declaration:  C  CON(J+2) = TE  (sec) exciter time constant
_DECL_RE = re.compile(
    r"(CON|STATE|VAR|ICON)\(\s*[JKLM]\s*(?:\+\s*(\d+))?\s*\)\s*=\s*(\w+)"
    r"\s*(?:\(([^)]*)\))?\s*(.*)", re.IGNORECASE)

_SUBROUTINE_RE = re.compile(r"SUBROUTINE\s+(\w+)", re.IGNORECASE)
_MODE_RE = re.compile(r"IF\s*\(\s*MODE\s*\.EQ\.\s*(\d+)\s*\)\s*THEN", re.IGNORECASE)

UNSUPPORTED = {
    "DO ": "DO loop — translate lookup/iteration manually",
    "GOTO": "GOTO — restructure control flow manually",
    "GO TO": "GOTO — restructure control flow manually",
    "DATA ": "DATA table — convert to DSL array/lapprox manually",
    "CALL ": "external CALL — locate callee and translate separately",
    "WRITE": "I/O statement — drop or replace with DSL event",
    "COMMON": "extra COMMON block — check for hidden shared state",
}


def _is_comment(line: str) -> bool:
    return bool(line) and line[0] in "Cc*!"


def _join_continuations(lines: list[str]) -> list[str]:
    """Fixed-form Fortran: any char in column 6 marks a continuation."""
    out: list[str] = []
    for line in lines:
        if len(line) > 5 and line[5] not in " 0" and not _is_comment(line):
            if out:
                out[-1] += " " + line[6:].strip()
                continue
        out.append(line.rstrip())
    return out


def parse_fortran_udm(path: str | Path) -> FortranUDM:
    """Parse a PSSE Fortran UDM source file into structured form."""
    path = Path(path)
    udm = FortranUDM(path=path)
    raw = path.read_text().splitlines()

    # Pass 1: header declarations from comments
    for line in raw:
        if not _is_comment(line):
            continue
        m = _DECL_RE.search(line)
        if not m:
            continue
        kind = m.group(1).upper()
        decl = Declaration(
            kind=kind,
            offset=int(m.group(2) or 0),
            name=m.group(3).upper(),
            unit=(m.group(4) or "").strip(),
            description=m.group(5).strip(),
        )
        {"CON": udm.cons, "STATE": udm.states,
         "VAR": udm.vars, "ICON": udm.icons}[kind].append(decl)

    # Pass 2: code statements, MODE-block dispatch
    code = _join_continuations(raw)
    current_mode: int | None = None
    skip_until_label: str | None = None
    for line in code:
        if _is_comment(line) or not line.strip():
            continue
        stmt = line.strip()

        # Inside an unsupported DO loop: collect body into warnings, skip emit
        if skip_until_label is not None:
            udm.warnings.append(f"  (in skipped DO body): `{stmt}`")
            label = line[:5].strip()
            if label == skip_until_label:
                skip_until_label = None
            continue

        m = _SUBROUTINE_RE.search(stmt)
        if m:
            udm.subroutine = m.group(1).upper()
            continue

        m = _MODE_RE.search(stmt)
        if m:
            current_mode = int(m.group(1))
            udm.mode_blocks.setdefault(current_mode, [])
            continue

        upper = stmt.upper()
        if upper.startswith(("ELSE", "ENDIF", "END IF")):
            if upper.startswith(("ENDIF", "END IF")):
                current_mode = None
            continue
        if upper.startswith(("RETURN", "END", "INTEGER", "REAL", "INCLUDE")):
            continue
        # slot pointer setup (J = STRTIN(...)) — bookkeeping, skip
        if re.match(r"[JKLM]\s*=\s*STRTIN", upper):
            continue

        unsupported = False
        for marker, why in UNSUPPORTED.items():
            if marker in upper:
                udm.warnings.append(f"{why}: `{stmt}`")
                unsupported = True
                break
        if unsupported:
            m = re.match(r"DO\s+(\d+)\s", upper)
            if m:
                skip_until_label = m.group(1)
            continue

        if current_mode is not None:
            udm.mode_blocks[current_mode].append(stmt)

    if not udm.mode_blocks:
        udm.warnings.append("No MODE blocks found — not a standard PSSE UDM skeleton")
    return udm
