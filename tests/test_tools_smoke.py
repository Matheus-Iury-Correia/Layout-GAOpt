"""Testes de fumaça do processo: contratos válidos, parser, normalização de erro e breaker.

Rodam desde o primeiro dia (Fase 0) e protegem a infraestrutura dos agentes.
"""
from __future__ import annotations

import os
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from _common import (  # noqa: E402
    REQUIRED_KEYS, VALID_TIERS, load_task, normalize_error, parse_mini_yaml,
)

TASK_IDS = sorted(p.stem for p in (ROOT / "tasks").glob("T-*.yaml"))


def test_there_are_phase1_contracts():
    assert TASK_IDS[:7] == [f"T-00{i}" for i in range(1, 8)]


def test_parse_template_and_flow_lists():
    data = parse_mini_yaml((ROOT / "tasks" / "_TEMPLATE.yaml").read_text(encoding="utf-8"))
    assert data["tier"] == "simple"
    assert data["memory_refs"] == ["ADR-003", "GLOSSARIO"]
    assert data["depends_on"] == []
    assert data["budget"]["max_attempts"] == 2
    assert isinstance(data["files_allowed"], list) and len(data["files_allowed"]) == 2


def test_mini_yaml_quotes_and_colons():
    data = parse_mini_yaml('a: "x: y"\nb: [1, "c, d", e]\nc:\n  - "item: com dois pontos"\n')
    assert data["a"] == "x: y"
    assert data["b"] == [1, "c, d", "e"]
    assert data["c"] == ["item: com dois pontos"]


@pytest.mark.parametrize("task_id", TASK_IDS)
def test_contract_is_valid(task_id):
    t = load_task(task_id)
    for key in REQUIRED_KEYS:
        assert t.get(key), f"{task_id}: campo obrigatório ausente: {key}"
    assert t["id"] == task_id
    assert t["tier"] in VALID_TIERS
    for dep in t["depends_on"]:
        assert dep in TASK_IDS, f"{task_id}: depends_on inexistente: {dep}"
    for cmd in t["acceptance_commands"]:
        assert str(cmd).split()[0] in ("pytest", "python"), f"{task_id}: comando de aceitação inválido"
    for k in ("max_attempts", "max_minutes", "max_tokens"):
        assert isinstance(t["budget"][k], int) and t["budget"][k] > 0
    for f in t["files_allowed"]:
        assert not any(fnmatch(f, pat) for pat in t["forbidden"]), f"{task_id}: {f} é permitido e proibido"
    assert len(t["files_allowed"]) == len(set(t["files_allowed"]))


def _ancestors(task_id: str, seen: set[str] | None = None) -> set[str]:
    seen = seen if seen is not None else set()
    for dep in load_task(task_id)["depends_on"]:
        if dep not in seen:
            seen.add(dep)
            _ancestors(dep, seen)
    return seen


def test_independent_tasks_have_disjoint_files():
    """Tarefas sem relação de dependência podem rodar em paralelo: files_allowed não pode colidir."""
    for i, a in enumerate(TASK_IDS):
        for b in TASK_IDS[i + 1:]:
            if a in _ancestors(b) or b in _ancestors(a):
                continue
            common = set(load_task(a)["files_allowed"]) & set(load_task(b)["files_allowed"])
            assert not common, f"{a} e {b} são independentes mas compartilham {sorted(common)}"


def test_dependencies_are_acyclic():
    for t in TASK_IDS:
        assert t not in _ancestors(t)


def test_normalize_error_ignores_numbers_but_not_test_names():
    a = "E   assert 3 == 4\nFAILED tests/a.py::test_x - AssertionError at 0x7f3a1c in /tmp/pytest-12/x"
    b = "E   assert 10 == 11\nFAILED tests/a.py::test_x - AssertionError at 0x9b2200 in /tmp/pytest-99/y"
    c = "E   assert 3 == 4\nFAILED tests/a.py::test_y - AssertionError at 0x7f3a1c in /tmp/pytest-12/x"
    assert normalize_error(a) == normalize_error(b)
    assert normalize_error(a) != normalize_error(c)


def _breaker(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, AGENT_STATE_DIR=str(tmp_path / "state"),
               ESCALATIONS_FILE=str(tmp_path / "esc.md"))
    return subprocess.run([sys.executable, str(ROOT / "tools" / "breaker.py"), *args],
                          capture_output=True, text=True, env=env)


def test_breaker_escalates_then_hands_off_then_calls_human(tmp_path):
    assert _breaker(tmp_path, "start", "T-001").returncode == 0
    r = _breaker(tmp_path, "record", "T-001", "--status", "fail", "--error-text", "FAILED a::t1 - E1")
    assert r.returncode == 0 and "RETRY" in r.stdout
    r = _breaker(tmp_path, "record", "T-001", "--status", "fail", "--error-text", "FAILED a::t2 - E2")
    assert r.returncode == 3 and "ESCALATE" in r.stdout
    assert "T-001" in (tmp_path / "esc.md").read_text(encoding="utf-8")

    assert _breaker(tmp_path, "handoff", "T-001").returncode == 0
    assert _breaker(tmp_path, "record", "T-001", "--status", "fail", "--error-text", "FAILED a::t3").returncode == 0
    r = _breaker(tmp_path, "record", "T-001", "--status", "fail", "--error-text", "FAILED a::t4")
    assert r.returncode == 4 and "HUMAN" in r.stdout


def test_breaker_detects_repeated_error(tmp_path):
    _breaker(tmp_path, "record", "T-999", "--status", "fail", "--error-text", "FAILED a::t - boom 1")
    r = _breaker(tmp_path, "record", "T-999", "--status", "fail", "--error-text", "FAILED a::t - boom 2")
    assert r.returncode == 3 and "mesmo erro" in r.stdout


def test_breaker_pass_and_handoff_guard(tmp_path):
    r = _breaker(tmp_path, "record", "T-002", "--status", "pass")
    assert r.returncode == 0 and r.stdout.startswith("OK")
    assert _breaker(tmp_path, "handoff", "T-002").returncode == 2


def test_verify_quick_runs(tmp_path):
    env = dict(os.environ, AGENT_STATE_DIR=str(tmp_path / "state"))
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "verify.py"), "--quick"],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "VERIFY: PASS" in r.stdout
