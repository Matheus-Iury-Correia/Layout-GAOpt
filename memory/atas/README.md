# Atas de tarefa

Cada tarefa concluída gera `memory/atas/T-xxx.md` (curta: no máximo ~25 linhas). Template:

```markdown
# T-xxx — <título>

- Data: AAAA-MM-DD
- Modelo/agente: <qual>
- Resultado: PASS | PASS com ressalvas | escalada
- Tentativas: N (escalou? sim/não)

## O que foi feito
<2 a 4 linhas>

## Decisões e armadilhas (o que o próximo agente precisa saber)
- <ex.: "rotação 90° troca largura/altura do pad; esqueci na 1ª tentativa">

## Pendências
- <ou "nenhuma">
```

Regras:
- Escreva **fatos úteis para o futuro**, não um diário.
- Se a decisão afeta interface ou arquitetura, **não** deixe só na ata: peça um ADR ao Arquiteto.
- Armadilhas recorrentes sobem para `memory/GLOSSARIO.md` ou para uma seção "Armadilhas" do `AGENTS.md`.
