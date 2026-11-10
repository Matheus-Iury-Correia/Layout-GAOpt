# Plano de convergência (requisito de primeira classe da Fase 3)

Objetivo: **entender como e por que o GA converge**, e não só obter um layout.
Uma execução de GA é uma amostra; **conclusão só com ≥ 10 sementes**.

## 1. Log por geração (JSONL)

Arquivo `experiments/<run_id>/log.jsonl`, uma linha por geração:

```json
{"run_id":"E2-elit-on-s07","seed":7,"gen":42,"evals_proxy":2100,"evals_router":210,
 "best":{"area":1.23e8,"hpwl":9.1e6,"vias":4,"unrouted":0,"hotloop":3.2e6},
 "mean":{"area":1.9e8,"hpwl":1.4e7,"vias":9.2,"unrouted":0.8,"hotloop":5.1e6},
 "hypervolume":0.612,"diversity":0.31,"routed_frac":0.84,
 "proxy_spearman":0.71,"elapsed_s":183.4}
```
Também `config.json` (todos os hiperparâmetros + versão do git) e `summary.md`.
Valores de objetivo em unidades internas (nm², nm).

## 2. Métricas

| Métrica | Definição | O que mostra |
|---|---|---|
| **Hypervolume** | Volume dominado pela frente de Pareto; ponto de referência = pior valor de cada objetivo na geração 0 × 1,1; objetivos normalizados | Convergência geral (principal) |
| **Melhor / média por objetivo** | Por geração | Velocidade e "folga" da população |
| **Diversidade** | Média, sobre pares de indivíduos, da distância média entre centros de componentes (normalizada pela diagonal da região) + fração de rotações diferentes | Perda de diversidade = convergência prematura |
| **% roteado** | Fração de indivíduos com 0 nets não roteadas | Viabilidade da população |
| **Spearman proxy × real** | A cada K gerações, 100–200 layouts roteados de verdade; correlação de ordem entre o proxy e a soma ponderada do roteador | **Se < ~0,5, o proxy engana o GA** (limiar inicial; ajustar com dados) |
| **Avaliações até o alvo** | Nº de avaliações (proxy e roteador separados) até atingir 95% do melhor hypervolume final | Custo da convergência |

## 3. Critérios de parada

- Hypervolume sem melhora relativa ≥ 0,1% por `N = 30` gerações (configurável); ou
- orçamento de tempo/avaliações; ou
- 100% roteado **e** estagnação.

## 4. Experimentos (todos com ≥ 10 sementes)

| ID | Pergunta | Variação |
|---|---|---|
| E0 | O GA vale mais que busca aleatória? | GA vs. random search, mesmas avaliações |
| E1 | Elitismo importa? | com/sem |
| E2 | Tamanho da população | 20 / 50 / 100 |
| E3 | Taxa de mutação (posição, rotação, ordem) | 3 níveis cada |
| E4 | A ordem de roteamento deve ser gene? | gene vs. ordem fixa vs. aleatória |
| E5 | O proxy basta? | só proxy vs. dois níveis; fração promovida ao roteador (10/25/50%) |
| E6 | Escala | 4, 10, 25, 50 componentes sintéticos: como cresce o custo até convergir |

Relatório: mediana e faixa interquartil das curvas; comparar grupos com Mann-Whitney U (scipy, opcional). Evitar concluir por uma execução.

## 5. Placas de validação

- **Sintéticas com referência:** `chain`, `star`, `random(n)` (T-004). Em `chain` há um layout de referência (fila compactada) e um limite inferior (soma das áreas dos courtyards). Use-os como régua: "o GA chega a X% do limite?".
- **Tutorial/público:** 1–3 placas pequenas para testar parser e roteador em geometria real.
- **Golden boards:** guardar métricas-base em `experiments/golden/` e comparar a cada mudança do motor para detectar regressões.

## 6. Testes que protegem a análise

- Mesmo `seed` + mesma `config` ⇒ **resultado idêntico** (determinismo).
- Invariantes I-1..I-8 verificadas em **toda** geração (modo debug).
- Elitismo ligado ⇒ o melhor valor de cada objetivo **não piora** entre gerações.
