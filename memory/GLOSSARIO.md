# Glossário

| Termo | Significado neste projeto |
|---|---|
| **nm** | Unidade interna: inteiro em nanômetros. |
| **Board** | Dados estáticos do projeto: componentes, nets, regras, setup. Não muda na otimização. |
| **Layout** | Estado evoluído pelo GA: posições/rotações + trilhas + vias. |
| **Placement** | Posição (x, y) e rotação de um componente. |
| **Courtyard** | Retângulo de exclusão em volta do componente; dois courtyards não podem se sobrepor. |
| **Netlist** | Conexões pad↔net. **Nunca muda** durante a otimização. |
| **Plano de GND** | Camada L1 (INNER1). Pads de GND ligam a ela por via curto, sem trilha. |
| **Hot loop** | Malha de comutação de potência (ex.: transistor, capacitor de bulk, diodo). Quanto menor a área, melhor. Nets definidas pelo usuário na GUI. |
| **HPWL** | Half-Perimeter Wire Length: soma, por net, do semiperímetro do retângulo que envolve os pads. Proxy barato de comprimento de trilha. |
| **Proxy** | Fitness rápido (área do bounding box, HPWL, sobreposição) usado antes do roteador. |
| **Roteador real** | Roteador de grade multicamada (A*) que produz trilhas e vias de verdade. Caro. |
| **Fitness em dois níveis** | Proxy filtra a população; só os melhores passam pelo roteador real. |
| **NSGA-II** | Algoritmo genético multiobjetivo; mantém uma frente de Pareto. |
| **Frente de Pareto** | Conjunto de soluções onde nenhum objetivo melhora sem piorar outro. |
| **Hypervolume** | Volume dominado pela frente de Pareto em relação a um ponto de referência. Principal métrica de convergência multiobjetivo. |
| **Diversidade** | Distância média entre layouts da população. Cai quando o GA converge (ou trava). |
| **Spearman (proxy × real)** | Correlação de ordem entre o proxy e o roteador real. Se for baixa, o GA converge para o lugar errado. |
| **Golden board** | Placa de referência com métricas-base para comparar versões do motor. |
| **Contrato (T-xxx)** | Arquivo YAML que delimita uma tarefa para um agente. |
| **Ata** | Registro curto, em `memory/atas/`, do que uma tarefa fez. |
| **Breaker** | `tools/breaker.py`; decide quando uma tarefa deve subir de nível ou parar. |
| **ESCALATE / HUMAN** | Saídas do breaker: subir para modelo mais forte / parar e chamar o humano. |
| **ODB++** | Formato aberto de intercâmbio de PCBs; adaptador de borda (Fase 4). |
