# pcb-compactor

Ferramenta local (Python) para **reduzir a área de PCBs** reposicionando componentes SMD e refazendo o roteamento com um **algoritmo genético**. A IA é usada **só no desenvolvimento**, por agentes (Freebuff) coordenados por contratos, memória em arquivos e verificação automática.

## Comece aqui

1. `docs/COMO_INICIAR_NO_FREEBUFF.md` — passo a passo (ambiente, git, sessões, ritual de cada tarefa).
2. `AGENTS.md` — as regras que todo agente lê.
3. `memory/adr/` — decisões (escopo, agentes, modelo canônico).
4. `tasks/` — contratos da Fase 1 (T-001 a T-007).

## Mapa do repositório

```
AGENTS.md                 regras para agentes
memory/                   ADRs, atas, glossário, log de escalonamentos
docs/                     roadmap, papéis/prompts, convergência, memória, checklist
tasks/                    contratos T-xxx.yaml (+ _TEMPLATE.yaml)
tools/verify.py           verificação (lint, escopo, aceitação, suíte) com saída resumida
tools/breaker.py          circuit breaker (tentativas, erro repetido, tempo, tokens)
engine/                   motor (model, geometry, synth, metrics, io; router e ga virão)
gui/                      interface PySide6 local
tests/                    testes (inclui validação dos contratos e das ferramentas)
experiments/              logs e resumos dos experimentos de convergência
.githooks/pre-push        roda o verify antes de push
```

## Comandos

```bash
pip install -e ".[dev]"
python tools/verify.py                         # suíte completa
python tools/verify.py --task T-001            # contrato + escopo + suíte
python tools/breaker.py status T-001
```

## Status

Fase 0 (esqueleto) pronta. Próxima: Fase 1 (`tasks/T-001`…`T-007`). Veja `docs/ROADMAP.md`.
