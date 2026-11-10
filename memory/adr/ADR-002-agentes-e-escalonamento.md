# ADR-002 — Agentes, tiers de tarefa e escalonamento

Status: **aceito**.

## Princípio

O **processo vive no repositório** (contratos, memória, verificação, breaker). O **executor é plugável**: hoje, agentes do Freebuff; amanhã, Claude Code, LangGraph ou outro. Nada neste repositório depende de um runner específico.

## Papéis

| Papel | Faz | Não faz |
|---|---|---|
| **Arquiteto** | ADRs, interfaces públicas, desenha a fase, revisa tarefas críticas | Implementar tarefas simples |
| **Decompositor** | Transforma a fase em contratos `tasks/T-xxx.yaml` | Escrever código de produção |
| **Executor** | Implementa **um** contrato, roda `verify`, escreve a ata | Tocar fora de `files_allowed`, mudar interface |
| **Revisor** | Lê só o diff e o contrato, verifica aderência (somente leitura) | Editar código |
| **Escalador** | Resolve o que o Executor não conseguiu, com contexto mínimo | Refazer a tarefa do zero |
| **Memorista** | Atualiza atas, glossário e índice da memória | Alterar código |

Prompts de cada papel em `docs/PAPEIS_AGENTES.md`.

## Tiers de tarefa (campo `tier` do contrato)

| Tier | Para quê | Quem executa |
|---|---|---|
| `critical` | Modelo canônico, geometria, robustez numérica, roteador, operadores do GA | **Melhor modelo disponível** (Pro/Opus/Sonnet) + revisão do humano nos ADRs |
| `standard` | Métricas, gerador sintético, GUI, integração | Modelo intermediário ou o forte, a critério do Arquiteto |
| `simple` | Serialização, testes, docstrings, boilerplate, refactors mecânicos | Modelo barato/rápido (ex.: V4 Flash) |

**Regra:** código geométrico (tolerâncias, clearance, sobreposição, rotação) **nunca** vai para o modelo barato sem revisão do Revisor com um modelo forte.

## Circuit breakers (`tools/breaker.py`)

Disparam **ESCALATE** quando qualquer condição for verdadeira:

1. `attempts >= budget.max_attempts` (padrão 2);
2. o **mesmo erro normalizado** (hash) aparece 2 vezes;
3. tempo desde o `start` > `budget.max_minutes`;
4. tokens reportados > `budget.max_tokens`;
5. o agente tocou arquivo proibido (detectado por `verify --task`).

Níveis: **0** Executor → **1** Escalador (modelo mais forte) → **2** humano. No nível 1, disparar de novo gera **HUMAN** (exit code 4) e a tarefa para. Todo escalonamento é registrado em `memory/ESCALONAMENTOS.md`.

## Aprovação automática e Git

- Agentes trabalham em `agent/T-xxx` a partir de `develop`.
- **Portão de merge em `develop`** (automático): `python tools/verify.py --task T-xxx` = PASS **e** a suíte completa verde **e** nenhum arquivo fora de `files_allowed`. Depois do merge, `verify` roda de novo em `develop`; se falhar, reverter o merge.
- **`develop` → `main` é humano**, com `docs/RELEASE_CHECKLIST.md`.
- Nunca `git push --force`, nunca reescrever histórico de `develop`/`main`.

## Memória

Fase atual: **arquivos versionados** (`memory/`). Cada tarefa produz uma **ata curta**; decisões viram **ADR**; termos viram **glossário**. Detalhes e critérios para adotar uma memória vetorial (mem0 local) em `docs/MEMORIA.md`.

## Rever quando houver modelo mais forte disponível

Mover o Arquiteto e o Revisor para ele; manter Executores baratos. Os contratos e o breaker não mudam.
