#!/usr/bin/env python3
"""Circuit breaker para tarefas de agentes.

Comandos:
    start    T-001                         inicia/reinicia o relógio e zera tentativas (nível 0)
    record   T-001 --status fail|pass      registra o resultado de uma tentativa
             [--error-file F | --error-text S] [--tokens N]
    handoff  T-001                         o Escalador (modelo mais forte) assume: zera tentativas, mantém nível
    status   T-001                         mostra o estado
    reset    T-001                         apaga o estado da tarefa

Saídas (e códigos de saída) do `record --status fail`:
    RETRY     (0)  pode tentar de novo
    ESCALATE  (3)  subir para modelo mais forte (nível 0 -> 1)
    HUMAN     (4)  o nível 1 também falhou: parar e chamar o humano

Dispara quando: tentativas >= max_attempts; mesmo erro normalizado 2x; tempo > max_minutes;
tokens > max_tokens. Limites vêm do bloco `budget:` do contrato (padrões: 2 / 45 min / 20000).
Se --error-file/--error-text faltarem, usa .agent_state/last_failure.txt (escrito pelo verify).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    BUDGET_DEFAULTS, escalations_file, load_task, normalize_error, state_dir,
)

EXIT_ESCALATE = 3
EXIT_HUMAN = 4


def state_path() -> Path:
    return state_dir() / "breaker.json"


def load_state() -> dict:
    p = state_path()
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def new_entry() -> dict:
    return {
        "started": time.time(), "attempts": 0, "hashes": [], "tokens": 0,
        "level": 0, "status": "open",
    }


def budget_for(task_id: str) -> dict:
    try:
        return load_task(task_id)["budget"]
    except FileNotFoundError:
        return dict(BUDGET_DEFAULTS)


def log_escalation(task_id: str, level_from: int, level_to: str, reasons: list[str]) -> None:
    path = escalations_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("# Registro de escalonamentos\n\n---\n", encoding="utf-8")
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"- {stamp} | {task_id} | nível {level_from} -> {level_to} | {'; '.join(reasons)}\n")


def cmd_start(args) -> int:
    state = load_state()
    state[args.task] = new_entry()
    save_state(state)
    b = budget_for(args.task)
    print(f"START {args.task}: máx {b['max_attempts']} tentativas, {b['max_minutes']} min, {b['max_tokens']} tokens")
    return 0


def read_error(args) -> str:
    if args.error_text:
        return args.error_text
    path = Path(args.error_file) if args.error_file else state_dir() / "last_failure.txt"
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def cmd_record(args) -> int:
    state = load_state()
    entry = state.setdefault(args.task, new_entry())
    entry["tokens"] += args.tokens or 0
    b = budget_for(args.task)

    if args.status == "pass":
        entry["status"] = "passed"
        save_state(state)
        print(f"OK {args.task}: passou na tentativa {entry['attempts'] + 1} (nível {entry['level']})")
        return 0

    entry["attempts"] += 1
    sig = normalize_error(read_error(args))
    h = hashlib.sha256(sig.encode("utf-8")).hexdigest()[:12]
    entry["hashes"].append(h)

    elapsed_min = (time.time() - entry["started"]) / 60
    reasons: list[str] = []
    if entry["attempts"] >= b["max_attempts"]:
        reasons.append(f"tentativas {entry['attempts']}/{b['max_attempts']}")
    if entry["hashes"].count(h) >= 2:
        reasons.append(f"mesmo erro repetido (hash {h})")
    if elapsed_min > b["max_minutes"]:
        reasons.append(f"tempo {elapsed_min:.0f}/{b['max_minutes']} min")
    if entry["tokens"] > b["max_tokens"]:
        reasons.append(f"tokens {entry['tokens']}/{b['max_tokens']}")

    if not reasons:
        save_state(state)
        left = b["max_attempts"] - entry["attempts"]
        print(f"RETRY {args.task}: tentativa {entry['attempts']} falhou (erro {h}); restam {left}")
        return 0

    reason_txt = "; ".join(reasons)
    if entry["level"] == 0:
        entry["status"] = "escalated"
        log_escalation(args.task, 0, "1", reasons)
        save_state(state)
        print(f"ESCALATE {args.task}: {reason_txt}")
        print("-> PARE. Escreva o pedido de escalonamento (docs/PAPEIS_AGENTES.md) e chame o Escalador.")
        return EXIT_ESCALATE

    entry["status"] = "human"
    log_escalation(args.task, entry["level"], "humano", reasons)
    save_state(state)
    print(f"HUMAN {args.task}: {reason_txt}")
    print("-> PARE. O escalonamento também falhou: o contrato ou um ADR provavelmente precisa mudar.")
    return EXIT_HUMAN


def cmd_handoff(args) -> int:
    state = load_state()
    entry = state.get(args.task)
    if not entry or entry["status"] != "escalated":
        print(f"ERRO: {args.task} não está em estado 'escalated'")
        return 2
    entry.update({"level": entry["level"] + 1, "attempts": 0, "hashes": [], "tokens": 0,
                  "started": time.time(), "status": "open"})
    save_state(state)
    print(f"HANDOFF {args.task}: nível {entry['level']}; contadores zerados")
    return 0


def cmd_status(args) -> int:
    entry = load_state().get(args.task)
    if not entry:
        print(f"{args.task}: sem estado")
        return 0
    b = budget_for(args.task)
    mins = (time.time() - entry["started"]) / 60
    print(
        f"{args.task}: {entry['status']} | nível {entry['level']} | tentativas {entry['attempts']}/{b['max_attempts']} "
        f"| {mins:.0f}/{b['max_minutes']} min | tokens {entry['tokens']}/{b['max_tokens']}"
    )
    return 0


def cmd_reset(args) -> int:
    state = load_state()
    state.pop(args.task, None)
    save_state(state)
    print(f"RESET {args.task}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("start", "handoff", "status", "reset"):
        sub.add_parser(name).add_argument("task")
    rec = sub.add_parser("record")
    rec.add_argument("task")
    rec.add_argument("--status", choices=["pass", "fail"], required=True)
    rec.add_argument("--error-file")
    rec.add_argument("--error-text")
    rec.add_argument("--tokens", type=int, default=0)
    args = ap.parse_args()
    return {"start": cmd_start, "record": cmd_record, "handoff": cmd_handoff,
            "status": cmd_status, "reset": cmd_reset}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
