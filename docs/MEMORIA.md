# Memória de longo prazo

## Camada 1 — arquivos versionados (agora)

| Onde | O quê | Quem escreve |
|---|---|---|
| `memory/adr/` | Decisões de arquitetura (imutáveis depois de aceitas; substituir por ADR novo) | Arquiteto, com aprovação do humano |
| `memory/atas/T-xxx.md` | O que cada tarefa fez, armadilhas, pendências | Executor |
| `memory/GLOSSARIO.md` | Termos do domínio | Memorista/Arquiteto |
| `memory/ESCALONAMENTOS.md` | Log automático do breaker | `tools/breaker.py` |
| `AGENTS.md` (seção Armadilhas, a criar quando houver 3+) | Erros recorrentes, para todo agente ler | Memorista, com aprovação do humano |

Vantagens: auditável, versionada no git, o agente carrega **só** o que o contrato referencia (`memory_refs`).

## Camada 2 — memória semântica local (quando precisar)

Adotar quando **qualquer** destes acontecer:
- mais de ~50 atas, e os agentes passam a repetir erros já registrados;
- o Arquiteto gasta contexto relendo muitas atas para achar uma decisão;
- começam a existir várias linhas de experimento do GA e você quer "o que já tentamos sobre X?".

Opção recomendada: **mem0 local** com um banco vetorial local (Qdrant ou Chroma) e embeddings que rodem na sua máquina. Indexar: atas, ADRs e `summary.md` dos experimentos. Regras:
- a memória vetorial é **índice**, a fonte de verdade continua nos arquivos;
- cada recuperação devolve **no máximo 3–5 trechos curtos** com o caminho do arquivo de origem;
- agentes citam o arquivo, e decisões importantes ainda viram ADR.

Não verifiquei a API atual do mem0; ao adotar, peça ao Arquiteto para ler a documentação vigente antes de escrever o contrato (será uma tarefa `standard`, no estilo `T-2xx`).

## Camada 3 — grafo de conhecimento (provavelmente desnecessária)

Só se surgir a necessidade de consultar relações ("qual ADR afeta quais contratos?"). Não antecipe.
