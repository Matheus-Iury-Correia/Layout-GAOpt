# ADR-001 — Escopo da prova de conceito e premissas

Status: **aceito** (decisões do usuário), com premissas marcadas `A-xxx` ainda a confirmar.
Mudanças só por novo ADR aprovado pelo humano.

## Objetivo

Reduzir a **área total** de uma PCB reposicionando componentes e refazendo o roteamento, com um **algoritmo genético (GA)**. O resultado é um **indicativo** para o engenheiro; o roteamento oficial (clearances, regras completas) continua sendo feito no Altium.

**Prioridade de aprendizado:** entender a **convergência** do GA (curvas, diversidade, correlação entre o proxy rápido e o roteador real) vale mais que a qualidade final da placa.

## Decisões (D)

| ID | Decisão |
|---|---|
| D-001 | IA **só no processo de desenvolvimento**. O produto (motor + GUI) não chama nenhum LLM. |
| D-002 | Tudo **local**, em **Python** (prova de conceito). Migrar partes quentes (roteador) para Rust/C++ só depois, se o Python não aguentar. |
| D-003 | GUI local em **PySide6** (`QGraphicsView`). Nada de web. |
| D-004 | Stackup fixo de **4 camadas**: L0 TOP (sinal), L1 INNER1 (**plano de GND**), L2 INNER2 (sinal), L3 BOTTOM (sinal). Número de camadas **não** é variável de otimização. |
| D-005 | Componentes **só SMD, só no TOP**. Rotação **0/90/180/270**. Trilhas podem usar L0, L2, L3. |
| D-006 | Pads de **GND** não são roteados: recebem um **via curto até o plano L1**, posto ao lado do pad (nunca dentro dele). |
| D-007 | Duas classes de net na prova de conceito: **sinal** e **potência**, com larguras parametrizadas. |
| D-008 | Componentes podem ser **congelados** (`locked`), por exemplo conectores de borda. Congelados não se movem nem giram. |
| D-009 | O usuário define na **GUI** o `OptimizationSetup`: componentes otimizáveis, região disponível, objetos bloqueados e a lista de nets do **hot loop**. |
| D-010 | Otimização **multiobjetivo** (NSGA-II) sobre área, vias, comprimento de trilha e proxy do hot loop. Fitness em **dois níveis**: proxy rápido e depois roteador real. |
| D-011 | Entrada/saída em **ODB++** é adaptador de borda (Fase 4). O motor trabalha com o **modelo canônico** (ADR-003). Não rodamos nada dentro do Altium. |
| D-012 | Escala de projeto: MCUs de 32–48 pinos e passivos 0402/0603/0805+. Prova de conceito com 3–4 componentes; depois 300–400. |
| D-013 | Hardware-alvo modesto (i5 antigo, GPU ignorada). Execuções de 1–2 h são aceitáveis. Use `os.cpu_count()`, `multiprocessing` e, se preciso, `numba` no laço quente. |

## Premissas (A) — a confirmar com o humano

| ID | Premissa | Valor inicial |
|---|---|---|
| A-001 | Distância **pad→via do GND**, de **borda a borda** (a confirmar se é essa a intenção; se for centro a centro, mudar). | 0,2 mm |
| A-002 | Um único `min_clearance` global para trilha/via/pad. | 0,2 mm |
| A-003 | Larguras de trilha (parametrizáveis). Sinal 1 mm não cabe entre pads 0402, então o padrão é menor. | sinal 0,25 mm / potência 1,0 mm |
| A-004 | Via padrão. | furo 0,3 mm / diâmetro 0,6 mm |
| A-005 | Margem do courtyard em volta dos pads. | 0,25 mm |

Valores ficam em `Rules` (ADR-003); nenhum número mágico no código.

## Fora de escopo (por enquanto)

Bottom como lado de componentes, through-hole, ângulos livres, impedância controlada, pares diferenciais, length matching, creepage/alta tensão, número de camadas variável, leitura direta de `.PcbDoc`, otimização dentro do Altium, qualquer LLM no produto.

## Teste de ida e volta com ODB++ (Fase 4)

Como não há placa real do usuário disponível agora, usar uma **placa de tutorial público** exportada em ODB++ (por exemplo, das demos do KiCad) para o primeiro teste de parser/escritor. Conferir depois o import no Altium como indicativo visual.
