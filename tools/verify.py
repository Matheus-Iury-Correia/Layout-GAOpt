#!/usr/bin/env python3
"""Verificador do repositório. Saída CURTA, pensada para economizar tokens de agentes.

Uso:
    python tools/verify.py                       # lint + suíte completa
    python tools/verify.py --task T-001          # + escopo do contrato + comandos de aceitação
    python tools/verify.py --task T-001 --quick  # sem a suíte completa
    python tools/verify.py --max-lines 60        # mais detalhe nas falhas

Saída final: "VERIFY: PASS" (exit 0) ou "VERIFY: FAIL" (exit 1).
A saída completa da última falha fica em .agent_state/last_failure.txt (usada pelo breaker).
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, load_task, state_dir, tail  # noqa: E402

ALWAYS_ALLOWED = ("memory/atas/*", "memory/ESCALONAMENTOS.md")


def run(cmd: list[str], timeout: int = 900) -> tuple[int, str]:
    try:
        p = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"TIMEOUT após {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError as exc:
        return 127, f"comando não encontrado: {exc}"


def summarize_pytest(out: str, max_lines: int) -> str:
    """Resumo curto: linhas FAILED/ERROR, linhas 'E ' (causa) e a linha final."""
    lines = out.splitlines()
    picked: list[str] = []
    for ln in lines:
        if ln.startswith(("FAILED", "ERROR")) or ln.startswith("E  "):
            if not picked or picked[-1] != ln.rstrip():  # evita linhas repetidas seguidas
                picked.append(ln.rstrip())
    final = next(
        (ln for ln in reversed(lines) if " passed" in ln or " failed" in ln or "error" in ln.lower()),
        "",
    )
    body = picked[: max(max_lines - 1, 1)]
    if len(picked) > len(body):
        body.append(f"... (+{len(picked) - len(body)} linhas; veja .agent_state/last_failure.txt)")
    if final:
        body.append(final.strip("= ").strip())
    return "\n".join("   " + b for b in body)


def changed_files(base: str) -> tuple[list[str] | None, str]:
    """Arquivos alterados em relação a `base` (commits + working tree + não rastreados)."""
    code, _ = run(["git", "rev-parse", "--is-inside-work-tree"], 30)
    if code != 0:
        return None, "não é repositório git"
    names: set[str] = set()
    cmds = [
        ["git", "diff", "--name-only", "HEAD"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    has_base, _ = run(["git", "rev-parse", "--verify", "--quiet", base], 30)
    if has_base == 0:
        cmds.append(["git", "diff", "--name-only", f"{base}...HEAD"])
    for c in cmds:
        code, out = run(c, 60)
        if code == 0:
            names.update(x.strip() for x in out.splitlines() if x.strip())
    return sorted(names), ("base=" + base if has_base == 0 else "sem branch base; só working tree")


def check_scope(task: dict, base: str) -> tuple[bool, str, str]:
    files, note = changed_files(base)
    if files is None:
        return True, f"escopo: SKIP ({note})", ""
    allowed = list(task["files_allowed"]) + list(ALWAYS_ALLOWED)
    forbidden = list(task["forbidden"])
    bad = []
    for f in files:
        if any(fnmatch(f, pat) for pat in forbidden) or not any(fnmatch(f, pat) for pat in allowed):
            bad.append(f)
    if bad:
        detail = "\n".join(f"   fora do escopo: {b}" for b in bad[:20])
        return False, f"escopo: {len(bad)} arquivo(s) fora de files_allowed ({note})", detail
    return True, f"escopo: {len(files)} arquivo(s) alterado(s), todos permitidos ({note})", ""


def acceptance_cmd(entry: str) -> list[str] | None:
    parts = shlex.split(entry)
    if not parts:
        return None
    if parts[0] == "pytest":
        return [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", *parts[1:]]
    if parts[0] == "python":
        return [sys.executable, *parts[1:]]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--task", help="ID do contrato, ex.: T-001")
    ap.add_argument("--base", default="develop", help="branch base para checar escopo")
    ap.add_argument("--quick", action="store_true", help="não roda a suíte completa")
    ap.add_argument("--max-lines", type=int, default=40)
    args = ap.parse_args()

    results: list[tuple[bool, str]] = []
    raw_failures: list[str] = []

    print(f"== verify {args.task or '(repositório)'} ==")

    # 1. lint
    code, out = run([sys.executable, "-m", "ruff", "--version"], 30)
    if code == 0:
        code, out = run([sys.executable, "-m", "ruff", "check", "."], 300)
        ok = code == 0
        results.append((ok, "lint (ruff)"))
        if not ok:
            raw_failures.append("== ruff ==\n" + out)
            print("[FAIL] lint (ruff)")
            print(tail(out, min(args.max_lines, 15)))
        else:
            print("[ ok ] lint (ruff)")
    else:
        print("[skip] lint (ruff não instalado: pip install -e .[dev])")

    # 2. contrato
    if args.task:
        task = load_task(args.task)
        ok, msg, detail = check_scope(task, args.base)
        results.append((ok, "escopo"))
        print(("[ ok ] " if ok else "[FAIL] ") + msg)
        if detail:
            print(detail)
            raw_failures.append("== escopo ==\n" + msg + "\n" + detail)

        for entry in task["acceptance_commands"]:
            cmd = acceptance_cmd(str(entry))
            if cmd is None:
                results.append((False, "aceitação"))
                print(f"[FAIL] aceitação: comando não permitido (use pytest/python): {entry}")
                raw_failures.append(f"== aceitação ==\ncomando não permitido: {entry}")
                continue
            code, out = run(cmd)
            ok = code == 0
            results.append((ok, f"aceitação: {entry}"))
            if ok:
                print(f"[ ok ] aceitação: {entry}")
            else:
                print(f"[FAIL] aceitação: {entry}")
                print(summarize_pytest(out, args.max_lines))
                raw_failures.append(f"== aceitação: {entry} ==\n" + out)

    # 3. suíte completa
    if not args.quick:
        code, out = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"])
        if "No module named pytest" in out:
            ok = False
            msg = "pytest não instalado (pip install -e .[dev])"
        elif code == 5:
            ok = False
            msg = "nenhum teste coletado"
        else:
            ok = code == 0
            msg = "suíte completa"
        results.append((ok, msg))
        if ok:
            final = next((ln for ln in reversed(out.splitlines()) if "passed" in ln), "")
            print(f"[ ok ] {msg}: {final.strip('= ').strip()}")
        else:
            print(f"[FAIL] {msg}")
            print(summarize_pytest(out, args.max_lines))
            raw_failures.append("== suíte completa ==\n" + out)

    failed = [r for r in results if not r[0]]
    sd = state_dir()
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "last_failure.txt").write_text(
        "\n\n".join(raw_failures) if failed else "", encoding="utf-8"
    )
    print("VERIFY: FAIL" if failed else "VERIFY: PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
