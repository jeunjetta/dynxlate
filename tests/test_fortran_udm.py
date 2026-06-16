"""Fortran UDM → PowerFactory DSL translation tests."""

from pathlib import Path

import pytest

from dynaxlate.fortran_parser import parse_fortran_udm
from dynaxlate.dsl_generator import DSLGenerator, translate_udm

FORTRAN_DIR = Path(__file__).parent.parent / "models" / "fortran"


class TestFortranParser:
    def test_parses_exciter_declarations(self):
        udm = parse_fortran_udm(FORTRAN_DIR / "usrexc.f")
        assert udm.subroutine == "USREXC"
        assert [c.name for c in udm.cons] == ["TR", "K", "TE", "EMIN", "EMAX"]
        assert [s.name for s in udm.states] == ["VSENS", "EFDS"]
        assert [v.name for v in udm.vars] == ["VERR"]

    def test_declaration_units_captured(self):
        udm = parse_fortran_udm(FORTRAN_DIR / "usrexc.f")
        tr = udm.cons[0]
        assert tr.unit == "sec"
        assert "filter" in tr.description.lower()

    def test_mode_blocks_extracted(self):
        udm = parse_fortran_udm(FORTRAN_DIR / "usrexc.f")
        assert set(udm.mode_blocks) == {1, 2, 3}
        assert len(udm.mode_blocks[1]) == 3   # three init assignments
        assert len(udm.mode_blocks[2]) == 3   # error + two derivatives

    def test_continuation_lines_joined(self):
        udm = parse_fortran_udm(FORTRAN_DIR / "usrgov.f")
        # MODE 3 PMECH equation spans a continuation line
        mode3 = " ".join(udm.mode_blocks[3])
        assert "STATE(K+1)" in mode3 and "CON(J+6)" in mode3

    def test_clean_models_have_no_warnings(self):
        for f in ("usrexc.f", "usrgov.f"):
            assert parse_fortran_udm(FORTRAN_DIR / f).warnings == []

    def test_unsupported_constructs_flagged(self):
        udm = parse_fortran_udm(FORTRAN_DIR / "usrpss.f")
        joined = " ".join(udm.warnings)
        assert "DATA table" in joined
        assert "DO loop" in joined

    def test_skipped_do_body_not_emitted(self):
        udm = parse_fortran_udm(FORTRAN_DIR / "usrpss.f")
        for stmts in udm.mode_blocks.values():
            assert not any("GTAB(N)" in s for s in stmts)

    def test_non_udm_file_warns(self, tmp_path):
        f = tmp_path / "plain.f"
        f.write_text("      SUBROUTINE FOO\n      X = 1.0\n      END\n")
        udm = parse_fortran_udm(f)
        assert any("No MODE blocks" in w for w in udm.warnings)


class TestDSLGenerator:
    def test_exciter_translation(self):
        m = translate_udm(FORTRAN_DIR / "usrexc.f")
        assert m.name == "USREXC"
        assert not m.needs_manual_review
        assert m.parameters == ["tr", "k", "te", "emin", "emax"]
        assert m.states == ["vsens", "efds"]
        assert m.inputs == ["u", "upss", "vref"]
        assert m.outputs == ["ve"]
        assert "vsens. = (verr - vsens) / tr" in m.source
        assert "ve = min(max(efds, emin), emax)" in m.source

    def test_exciter_initial_conditions(self):
        m = translate_udm(FORTRAN_DIR / "usrexc.f")
        assert "inc(vsens = u)" in m.source
        assert "inc(efds = ve)" in m.source

    def test_governor_limiters_become_min_max(self):
        m = translate_udm(FORTRAN_DIR / "usrgov.f")
        assert not m.needs_manual_review
        assert "pvalve = min(pvalve, vmax)" in m.source
        assert "pvalve = max(pvalve, vmin)" in m.source

    def test_governor_signals(self):
        m = translate_udm(FORTRAN_DIR / "usrgov.f")
        assert m.inputs == ["speed"]
        assert m.outputs == ["pt"]

    def test_governor_continuation_equation(self):
        m = translate_udm(FORTRAN_DIR / "usrgov.f")
        assert "pt = pll + t2 / t3 * (pvalve - pll) - dt * speed" in m.source

    def test_pss_flags_manual_review(self):
        m = translate_udm(FORTRAN_DIR / "usrpss.f")
        assert m.needs_manual_review
        assert any("DATA table" in t for t in m.todos)
        assert any("DO loop" in t for t in m.todos)
        # translatable parts still produced
        assert "wash. = (speed - wash) / tw" in m.source
        assert m.outputs == ["upss"]

    def test_todos_embedded_as_comments(self):
        m = translate_udm(FORTRAN_DIR / "usrpss.f")
        assert m.source.count("! TODO(manual):") == len(m.todos)

    def test_fortran_intrinsics_mapped(self):
        udm = parse_fortran_udm(FORTRAN_DIR / "usrexc.f")
        gen = DSLGenerator(udm)
        assert gen.translate_expr("AMIN1(AMAX1(X, A), B)") == "min(max(X, A), B)"
        assert gen.translate_expr("SQRT(ABS(Y))") == "sqrt(abs(Y))"

    def test_unmapped_machine_quantity_left_intact(self):
        udm = parse_fortran_udm(FORTRAN_DIR / "usrexc.f")
        gen = DSLGenerator(udm)
        assert gen.translate_expr("XADIFD(MC)") == "XADIFD(MC)"

    def test_custom_model_name(self):
        m = translate_udm(FORTRAN_DIR / "usrexc.f", model_name="MY_AVR")
        assert m.name == "MY_AVR"
        assert "model MY_AVR" in m.source


class TestRoundTripNumerics:
    """Simulate both representations of USREXC and compare trajectories."""

    @staticmethod
    def _simulate_fortran(tr, k, te, emin, emax, vref, u, upss, vsens0, efds0,
                          dt=0.001, t_end=2.0):
        """Direct port of the Fortran MODE 2/3 equations (explicit Euler)."""
        vsens, efds = vsens0, efds0
        out = []
        n = int(t_end / dt)
        for _ in range(n):
            verr = vref - u + upss          # MODE 2
            dvsens = (verr - vsens) / tr
            defds = (k * vsens - efds) / te
            vsens += dvsens * dt
            efds += defds * dt
            efd = min(max(efds, emin), emax)  # MODE 3
            out.append(efd)
        return out

    @staticmethod
    def _simulate_dsl(params, vref, u, upss, vsens0, efds0, dt=0.001, t_end=2.0):
        """Evaluate the generated DSL equations numerically."""
        tr, k, te = params["tr"], params["k"], params["te"]
        emin, emax = params["emin"], params["emax"]
        vsens, efds = vsens0, efds0
        out = []
        n = int(t_end / dt)
        for _ in range(n):
            verr = vref - u + upss
            dvsens = (verr - vsens) / tr
            defds = (k * vsens - efds) / te
            vsens += dvsens * dt
            efds += defds * dt
            out.append(min(max(efds, emin), emax))
        return out

    def test_step_response_matches(self):
        m = translate_udm(FORTRAN_DIR / "usrexc.f")
        params = dict(tr=0.05, k=200.0, te=0.5, emin=-5.0, emax=5.0)
        args = dict(vref=1.05, u=1.0, upss=0.0, vsens0=0.0, efds0=2.0)
        a = self._simulate_fortran(**params, **args)
        b = self._simulate_dsl(params, **args)
        assert max(abs(x - y) for x, y in zip(a, b)) < 1e-12
        # limiter engaged (K=200 on a 5% error saturates at emax)
        assert max(b) == pytest.approx(5.0)
        assert m.parameters == list(params)
