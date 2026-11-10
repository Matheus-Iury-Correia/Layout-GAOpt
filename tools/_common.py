"""Utilitários compartilhados por verify.py e breaker.py (somente biblioteca padrão)."""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"

REQUIRED_KEYS = (
    "id", "title", "tier", "goal", "files_allowed", "acceptance_commands", "budget",
)
VALID_TIERS = ("critical", "standard", "simple")
LIST_KEYS = (
    "depends_on", "memory_refs", "files_allowed", "forbidden", "signatures",
    "spec", "acceptance_commands", "acceptance_notes",
)
BUDGET_DEFAULTS = {"max_attempts": 2, "max_minutes": 45, "max_tokens": 20000}


def state_dir() -> Path:
    """Pasta de estado local (ignorada pelo git). Pode ser trocada por AGENT_STATE_DIR."""
    return Path(os.environ.get("AGENT_STATE_DIR", ROOT / ".agent_state"))


def escalations_file() -> Path:
    return Path(os.environ.get("ESCALATIONS_FILE", ROOT / "memory" / "ESCALONAMENTOS.md"))


# ---------------------------------------------------------------- mini YAML
def _scalar(text: str):
    s = text.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    return s


def _split_flow(text: str) -> list:
    inner = text.strip()[1:-1]
    items: list[str] = []
    cur = ""
    quote = None
    for ch in inner:
        if quote:
            cur += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            cur += ch
        elif ch == ",":
            items.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        items.append(cur)
    return [_scalar(i) for i in items]


def parse_mini_yaml(text: str) -> dict:
    """Parser do subconjunto de YAML usado nos contratos (veja tasks/_TEMPLATE.yaml)."""
    data: dict = {}
    cur_key = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if '"' not in line and "'" not in line:
            line = re.sub(r"\s+#.*$", "", line)
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        if indent == 0:
            m = re.match(r"([A-Za-z_][\w-]*):\s*(.*)$", body)
            if not m:
                raise ValueError(f"linha inválida no contrato: {raw!r}")
            key, val = m.groups()
            cur_key = key
            if val == "":
                data[key] = None
            elif val.startswith("["):
                data[key] = _split_flow(val)
            else:
                data[key] = _scalar(val)
        else:
            if cur_key is None:
                raise ValueError(f"linha indentada sem chave: {raw!r}")
            if body.startswith("- "):
                if not isinstance(data[cur_key], list):
                    data[cur_key] = []
                data[cur_key].append(_scalar(body[2:]))
            else:
                m = re.match(r"([A-Za-z_][\w-]*):\s*(.*)$", body)
                if not m:
                    raise ValueError(f"linha inválida no contrato: {raw!r}")
                if not isinstance(data[cur_key], dict):
                    data[cur_key] = {}
                data[cur_key][m.group(1)] = _scalar(m.group(2))
    return data


def load_task(task_id: str) -> dict:
    path = TASKS_DIR / f"{task_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"contrato não encontrado: {path}")
    data = parse_mini_yaml(path.read_text(encoding="utf-8"))
    for key in LIST_KEYS:
        if data.get(key) is None:
            data[key] = []
    budget = dict(BUDGET_DEFAULTS)
    if isinstance(data.get("budget"), dict):
        budget.update(data["budget"])
    data["budget"] = budget
    return data


# ------------------------------------------------------------------- erros
def normalize_error(text: str) -> str:
    """Reduz uma saída de falha a uma 'assinatura' estável (ignora números, endereços, tmp)."""
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    lines = text.splitlines()
    keep = [ln for ln in lines if ln.startswith(("FAILED", "ERROR", "E  "))]
    if not keep:
        keep = lines[-20:]
    s = "\n".join(keep).lower()
    s = re.sub(r"0x[0-9a-f]+", "0x", s)
    s = re.sub(r"/tmp/[^\s:]+", "/tmp", s)
    s = re.sub(r"\b\d+(\.\d+)?\b", "N", s)
    return re.sub(r"\s+", " ", s).strip()


def tail(text: str, n: int) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-n:])
