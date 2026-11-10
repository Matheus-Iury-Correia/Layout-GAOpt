# ADR-003 — Modelo canônico de dados

Status: **aceito**. Interface pública: só muda por novo ADR.

Tudo no motor (roteador, GA, métricas, GUI) enxerga **apenas** este modelo. ODB++ e outros formatos são adaptadores de borda.

## Convenções

- **Unidades:** inteiros em **nm** (1 mm = 1_000_000 nm). Helper `mm(x) -> int` em `engine/model`.
- **Eixos:** X para a direita, **Y para cima**. Origem arbitrária. Ângulos **anti-horários**.
- **Rotação de um componente** (ângulo θ ∈ {0, 90, 180, 270}): rotaciona os pontos do footprint em torno da origem do componente, **depois** soma a posição. Para 90°: `(x, y) → (-y, x)`. Retângulos giram exatamente (AABB troca largura/altura em 90° e 270°).
- **Camadas:** `L0 TOP`, `L1 GND_PLANE`, `L2 INNER2`, `L3 BOTTOM`. Roteável: L0, L2, L3. L1 é plano (sem trilhas).
- Estruturas imutáveis (`@dataclass(frozen=True)`) para dados de projeto; o `Layout` é substituído, não mutado, a cada indivíduo do GA.

## Entidades

```
Point(x:int, y:int)
Rect(x0:int, y0:int, x1:int, y1:int)            # x0<x1, y0<y1; helpers: width, height, area, intersects, union

PadShape: "rect" | "circle"                       # prova de conceito: rect
Pad(name:str, offset:Point, size:(int,int), shape:PadShape)   # frame local do footprint
Footprint(name:str, pads:tuple[Pad,...], courtyard:Rect)      # courtyard no frame local

Component(ref:str, footprint:Footprint)           # estático (sem posição)
NetClass: "signal" | "power" | "gnd_plane"
Net(name:str, net_class:NetClass, pins:tuple[PinRef,...])     # PinRef(ref:str, pad:str)
Rules(min_clearance:int, pad_via_gap:int, via_drill:int, via_diameter:int,
      width_signal:int, width_power:int, courtyard_margin:int)

OptimizationSetup(
    optimizable: frozenset[str],                  # refs que o GA pode mover
    locked: frozenset[str],                       # refs congelados (interseção com optimizable = vazio)
    region: Rect,                                 # área onde componentes podem ficar
    hot_loop_nets: tuple[str,...],                # definido pelo usuário na GUI
    blocked: tuple[Rect,...] = ())                # áreas proibidas

Board(name:str, components:tuple[Component,...], nets:tuple[Net,...],
      rules:Rules, setup:OptimizationSetup)       # tudo que NÃO muda durante a otimização

Placement(x:int, y:int, rotation:int)             # lado = TOP implícito
Track(net:str, layer:int, a:Point, b:Point, width:int)        # segmento reto, ortogonal ou 45°
Via(net:str, at:Point, drill:int, diameter:int, layers:(int,int))
Layout(placements:dict[str,Placement], tracks:tuple[Track,...], vias:tuple[Via,...])   # o que o GA evolui
```

## Funções públicas obrigatórias (`engine/model` e `engine/geometry`)

- `pad_center(board, layout, ref, pad) -> Point`
- `component_courtyard(board, layout, ref) -> Rect` (já rotacionado e transladado)
- `netlist_hash(board) -> str` (sha256 hex)
- `validate_board(board) -> list[str]` e `validate_layout(board, layout) -> list[str]` (lista vazia = válido)

## Invariantes (testadas por propriedade em `tests/properties/`)

| ID | Invariante |
|---|---|
| I-1 | Toda coordenada e dimensão é `int` (nunca `float`). |
| I-2 | `rotation ∈ {0, 90, 180, 270}`. |
| I-3 | Todo `PinRef` aponta para componente e pad existentes; nenhum pad em duas nets. |
| I-4 | `netlist_hash(board)` é idêntico antes e depois de qualquer operação do motor. |
| I-5 | Toda `Track`/`Via` referencia uma net existente. |
| I-6 | Componente em `locked` **nunca** muda de `Placement` ao longo da otimização. |
| I-7 | Todo componente otimizável tem o courtyard dentro de `setup.region` e fora de `setup.blocked`. |
| I-8 | Serializar e desserializar (`to_json`/`from_json`) devolve objeto **igual** (round-trip exato). |

## `netlist_hash`

sha256 sobre as linhas ordenadas `"<net>|<ref>.<pad>"`, uma por pino, separadas por `\n`, mais as linhas `"CLASS|<net>|<net_class>"`. Independe da ordem de declaração.

## Formato JSON (resumo; detalhe na tarefa T-003)

```json
{"format":"pcbc-1","board":{...},"layout":{...}}
```
Chaves ordenadas, indentação fixa, sem floats. Campo `format` permite evoluir.
