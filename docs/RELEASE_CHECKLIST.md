# Checklist de release (`develop` → `main`) — aprovação humana

Faça na sua máquina, em `develop` atualizada.

- [ ] `python tools/verify.py` → `VERIFY: PASS` (suíte completa).
- [ ] `memory/ESCALONAMENTOS.md`: algum escalonamento novo sem ata explicando a causa?
- [ ] Atas novas existem para todas as tarefas mescladas.
- [ ] Abrir a GUI/viewer com 1 placa sintética e 1 de tutorial: visual coerente (sem componentes sobrepostos, locked parados, tudo dentro da região).
- [ ] Rodar o experimento-padrão com **uma** semente: não quebra, gera `log.jsonl` e `summary.md`.
- [ ] Comparar com `experiments/golden/`: nenhuma métrica-base piorou sem justificativa em ata/ADR.
- [ ] Invariantes (I-1..I-8) verdes também em modo debug.
- [ ] Nenhum dado real de cliente/projeto no repositório (`git grep` por nomes e caminhos).
- [ ] `git log develop ^main --oneline` revisado: mensagens coerentes (`T-xxx: ...`).

Se tudo marcado: `git checkout main && git merge --no-ff develop && git tag vX.Y.Z`.
