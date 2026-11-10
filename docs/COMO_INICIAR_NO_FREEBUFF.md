# Como iniciar no Freebuff

Guia passo a passo. Leia uma vez, depois use como roteiro.

## 0. O que o Freebuff é (e as limitações que importam)

- Agente de código gratuito, mantido por anúncios, com CLI (`npm install -g freebuff`), versão Desktop (agentes paralelos locais) e outras. Baseado no framework Codebuff.
- O catálogo de modelos (DeepSeek V4 Pro/Flash e outros) e os limites de sessão **mudam**; confira no seletor. O V4 Flash pode **pausar em horário de pico**.
- **Privacidade:** prompts podem ser analisados para anúncios. Neste projeto, trabalhamos só com código e placas sintéticas/de tutorial. **Não cole dados de placas reais do seu trabalho.**
- O Freebuff Desktop pode rodar o Claude Code instalado na sua máquina usando a sua conta; se tiver, esse é o seu "modelo forte" (Arquiteto/Escalador/Revisor).

## 1. Preparar a máquina (uma vez)

```bash
# Python 3.10+ e git instalados
cd pcb-compactor
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"                                # pytest, ruff, numpy
# opcional, só quando chegar na GUI e no GA:
# pip install -e ".[gui,ga]"
```

## 2. Inicializar o git

```bash
git init -b main
git add -A && git commit -m "chore: esqueleto do repositório"
git checkout -b develop
git config core.hooksPath .githooks        # liga o hook de pre-push (roda o verify)
python tools/verify.py                      # deve imprimir VERIFY: PASS
```

Se o `verify` não passar aqui, **não comece**: o ambiente está errado.

## 3. Abrir o Freebuff

```bash
cd pcb-compactor
freebuff
```

Na primeira mensagem de **toda** sessão, indique o papel (veja `docs/PAPEIS_AGENTES.md`). Se o Freebuff não carregar o `AGENTS.md` sozinho, a primeira linha do prompt deve ser: "Leia AGENTS.md antes de qualquer coisa."

## 4. Sessões iniciais (nesta ordem)

### Sessão A — Arquiteto revisa as decisões (modelo forte, ~15 min)
```
[prompt do Arquiteto] Leia ADR-001, ADR-002 e ADR-003 e docs/ROADMAP.md. NÃO escreva código.
Entregue: (1) inconsistências ou lacunas que você achar; (2) riscos técnicos que faltam;
(3) se o modelo canônico do ADR-003 serve para o roteador de grade e para o GA (cromossomo =
posições + rotações + ordem de roteamento das nets); (4) perguntas numeradas ao humano.
```
Você responde as perguntas; mudanças viram **ADR novo** (não edite os aceitos).

### Sessão B — Decompositor valida a Fase 1 (modelo forte, ~10 min)
```
[prompt do Decompositor] Revise tasks/T-001..T-007 contra os ADRs. Corrija o que estiver
ambíguo, mantendo o formato do _TEMPLATE.yaml. Rode pytest tests/test_tools_smoke.py.
```

### Sessões C em diante — uma por tarefa

Ordem e modelo:

| Ordem | Tarefa | Tier | Modelo | Paralelizável? |
|---|---|---|---|---|
| 1 | T-001 modelo canônico | critical | forte | não |
| 2 | T-002 geometria | critical | forte | não (depende de T-001) |
| 3 | T-003 serialização JSON | simple | rápido | **sim**, com T-004 e T-005 |
| 3 | T-004 gerador sintético | standard | intermediário/forte | **sim** |
| 3 | T-005 métricas proxy | standard | intermediário/forte | **sim** |
| 4 | T-006 viewer PySide6 | standard | intermediário | depende de T-003 |
| 5 | T-007 propriedades/metamórficos | standard | forte | depende de T-004 e T-005 |

Depois de cada tarefa `critical`, rode uma sessão do **Revisor** (modelo forte) sobre o diff antes do merge.

## 5. Ritual de cada sessão de Executor

```
[prompt do Executor] Sua tarefa: T-00X.
```
O Executor segue o fluxo do `AGENTS.md`. Você só acompanha. Se ele imprimir ESCALATE ou escrever um pedido de escalonamento:

1. Abra uma sessão nova, **modelo mais forte**, prompt do **Escalador**, e cole o pedido de escalonamento. Nada mais: sem o histórico da sessão anterior.
2. Se o Escalador também falhar (`HUMAN`), a tarefa é sua: normalmente o contrato ou um ADR precisa mudar.

## 6. Portão de merge para `develop`

Rode (você ou uma sessão do Executor) na branch da tarefa:

```bash
python tools/verify.py --task T-00X --base develop      # tudo verde?
git checkout develop
git merge --no-ff agent/T-00X -m "merge T-00X"
python tools/verify.py                                  # suíte completa em develop
# se falhar:   git revert -m 1 HEAD   (desfaz o merge) e volte a tarefa para o Executor
```
O merge é **automático** porque a aprovação é a suíte de testes, não o humano. Você só aprova `develop` → `main` (`docs/RELEASE_CHECKLIST.md`).

## 7. Paralelismo (Freebuff Desktop)

Só rode tarefas em paralelo se os `files_allowed` forem **disjuntos** (T-003, T-004 e T-005 são). Use uma branch (ou `git worktree`) por tarefa. Cuidado com custo e limites de sessão: no início, **uma ou duas** em paralelo bastam.

## 8. Problemas comuns

| Sintoma | O que fazer |
|---|---|
| Agente lê o repo inteiro e gasta contexto | Lembrar: "leia só o contrato e os memory_refs". Sessão nova por tarefa. |
| Agente editou arquivo fora do escopo | `verify --task` acusa. `git checkout -- <arquivo>` e reabrir. Contar como falha no breaker. |
| Flash pausado em horário de pico | Usar o Pro para tarefas `simple` (custa mais tokens, mas anda) ou esperar. |
| Mesmo erro em loop | O breaker já deve ter escalado. Se não, rode `python tools/breaker.py record T-00X --status fail`. |
| Teste estocástico "às vezes passa" | É bug do teste: faltou semente fixa. Tarefa para o Arquiteto/Executor forte. |
| Contexto da sessão ficou enorme | Encerrar, abrir outra sessão com o contrato e a ata. A memória está nos arquivos. |

## 9. Depois da Fase 1

Peça ao Arquiteto: "Escreva o ADR da Fase 2 (roteador de grade multicamada) e o Decompositor gera os contratos T-1xx". A Fase 2 é `critical` quase inteira. Veja `docs/ROADMAP.md`.
