# Roadmap

Cada fase termina com um critério **verificável**. Contratos das Fases 2+ são escritos pelo Decompositor quando a fase anterior fechar (não antes: o aprendizado da fase anterior muda o desenho).

## Fase 0 — Esqueleto (este repositório)
ADRs, contratos da Fase 1, `verify`, `breaker`, memória em arquivos.
**Pronto quando:** `python tools/verify.py` imprime PASS na sua máquina.

## Fase 1 — Fundação (T-001 a T-007)
Modelo canônico, geometria, serialização JSON, gerador de placas sintéticas, métricas proxy, viewer PySide6, testes de propriedade.
**Pronto quando:** `make_chain_board(...)` gera uma placa; as métricas calculam; o viewer a mostra; invariantes I-1..I-8 verdes.

## Fase 2 — Roteador
Roteador de grade multicamada (A*, custo por via, L0/L2/L3), fanout de GND ao plano L1 respeitando `pad_via_gap` (A-001), classes sinal/potência, ordem das nets como parâmetro, validação de conectividade (netlist nunca muda), contagem de nets não roteadas.
**Risco principal:** desempenho em Python. Medir cedo com 50 componentes sintéticos antes de otimizar; `numba` no laço quente se preciso.
**Pronto quando:** roteia as placas sintéticas e uma placa de tutorial com 100% de nets (ou reporta exatamente quais falharam), com testes de propriedade.

## Fase 3 — Algoritmo genético
Cromossomo (x, y, rotação por componente + permutação de nets), operadores respeitando `locked`/`region`/`blocked`, NSGA-II (pymoo ou DEAP), fitness em dois níveis, **instrumentação de convergência completa** (`docs/PLANO_CONVERGENCIA.md`), runner de experimentos com várias sementes.
**Pronto quando:** em placas sintéticas de cadeia, o GA chega a ≤ X% (definir no ADR) do layout de referência em N gerações, em ≥ 80% das sementes; as curvas e a correlação proxy×real são geradas automaticamente.

## Fase 4 — Entrada e saída ODB++ + GUI de setup
Adaptador ODB++ (leitura e escrita), teste de ida e volta com placa de tutorial, importação no Altium como indicativo. GUI de `OptimizationSetup` (selecionar otimizáveis, congelar, região, objetos bloqueados, nets do hot loop) e visualização antes/depois, curvas ao vivo.
**Pronto quando:** abrir ODB++ → configurar setup → rodar GA → exportar ODB++ → o engenheiro vê o resultado no Altium.

## Fase 5 — Escala (300–400 componentes)
Agrupamento hierárquico por clusters funcionais, avaliação incremental, paralelismo (`multiprocessing`), migração do laço quente para Rust/C++ se necessário, clearance de alta tensão e creepage (eletrônica de potência), regras elétricas mais completas.

## Paralelo: memória
Começa em arquivos (`memory/`). Considerar mem0 local quando os critérios de `docs/MEMORIA.md` forem atingidos.
