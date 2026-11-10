# AGENTS.md — regras para qualquer agente neste repositório

Leia este arquivo inteiro antes de agir. Ele vale para todos os agentes e modelos (Arquiteto, Executor, Revisor, etc.).

## O projeto em 5 linhas

Ferramenta **local, em Python**, que reduz a **área total de uma PCB** reposicionando componentes SMD (só no top, rotação em múltiplos de 90°) e refazendo o roteamento das trilhas, usando um **algoritmo genético**. IA existe **apenas no processo de desenvolvimento**, nunca dentro do produto. O resultado serve de indicativo para o engenheiro refazer o roteamento oficial no Altium. **O objetivo principal é entender a convergência do GA**, não entregar uma placa perfeita.

## Antes de começar qualquer tarefa

1. Leia `memory/adr/` (ADR-001, ADR-002, ADR-003) e `memory/GLOSSARIO.md`.
2. Leia **o seu contrato**: `tasks/T-xxx.yaml`. Ele define o seu escopo, e nada além dele.
3. **Não leia o repositório inteiro.** Leia só o que o contrato referencia (`memory_refs`, `files_allowed` e o que esses arquivos importam). Contexto pequeno é requisito, não preferência.

## Regras invioláveis

- Edite **somente** os arquivos de `files_allowed`. Nunca toque em `forbidden`. Se precisar mexer fora do escopo, **pare** e escreva um pedido de escalonamento (veja `docs/PAPEIS_AGENTES.md`).
- **Unidades:** coordenadas e dimensões são **inteiros em nanômetros (nm)**. Nunca armazene `float` de coordenada. Floats só em cálculo intermediário, convertidos com `round()`.
- **Rotação:** somente 0, 90, 180, 270 (anti-horário). **Lado:** somente TOP nesta fase.
- **Determinismo:** toda aleatoriedade vem de um gerador passado por argumento (`random.Random(seed)` ou `numpy.random.Generator`). **Proibido** `random.random()` global, `np.random.seed()` e similares.
- **A netlist nunca muda.** Nenhuma função do motor cria, remove ou altera nets nem as conexões pad↔net. Existe teste para isso (`netlist_hash`).
- **Sem dependências novas** sem registrar em ADR. O ambiente pode estar sem internet; use o que `pyproject.toml` já lista.
- **Sem dados reais de projetos ou clientes.** Só placas sintéticas ou de tutoriais públicos. O Freebuff pode analisar prompts para anúncios, então nada confidencial em chat.
- Type hints em tudo que for público. Comentários em português, identificadores em inglês.
- **Não "melhore" o que não foi pedido.** Sem refatorações fora do contrato, sem renomear, sem reformatar arquivos alheios.

## Fluxo de uma tarefa

```
1. git checkout develop && git checkout -b agent/T-xxx
2. python tools/breaker.py start T-xxx
3. Escreva/rode os testes de aceitação primeiro, depois implemente.
4. python tools/verify.py --task T-xxx
5a. FAIL -> python tools/breaker.py record T-xxx --status fail
        - imprimiu "RETRY"     -> corrija e volte ao passo 4
        - imprimiu "ESCALATE"  -> PARE. Siga "Escalonamento" abaixo.
5b. PASS -> python tools/breaker.py record T-xxx --status pass
        - escreva memory/atas/T-xxx.md (template em memory/atas/README.md)
        - git add -A && git commit -m "T-xxx: <resumo curto>"
6. NÃO faça merge em main. Merge em develop só pelo portão (docs/COMO_INICIAR_NO_FREEBUFF.md, seção 6).
```

## O que devolver ao terminar (resposta curta)

- `git diff --stat` e o resultado de `verify` (as últimas linhas bastam);
- uma nota de **no máximo 3 linhas**: o que foi feito, o que ficou de fora, qualquer dúvida;
- **não** cole arquivos inteiros na resposta e **não** recapitule os passos.

## Escalonamento

Pare e peça ajuda quando: o `breaker` imprimir `ESCALATE`; o contrato for ambíguo ou contraditório; for preciso tocar arquivo fora de `files_allowed`; ou você perceber que está tentando a mesma correção pela terceira vez. Ao escalar, entregue: o contrato, as últimas ~40 linhas do erro (`.agent_state/last_failure.txt`), `git diff --stat` e **3 linhas** do que já foi tentado. Nada além disso.

## Quando estiver em dúvida

Prefira **perguntar/escalar** a inventar uma interface. Interfaces públicas (assinaturas em `signatures`, formato do JSON, campos do modelo) só mudam por ADR.
