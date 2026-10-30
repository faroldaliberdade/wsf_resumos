# Resumos WSF

Acervo de resumos temáticos das lives de **Weintraub sem Filtro**, **Raiz Cristã** e programas **Especiais**.

## Estrutura

- `wsf/` — episódios numerados do Weintraub sem Filtro.
- `rc/` — resumos da Raiz Cristã.
- `especiais/` — programas especiais.
- `index.html` — catálogo com busca e filtros por programa.
- `assets/` — estilos e comportamento do catálogo.
- `tools/build_index.py` — regenera o catálogo a partir das páginas.

## Atualizar o catálogo

```bash
python3 tools/build_index.py
```

O gerador lê o título, a URL do vídeo e o primeiro tópico de cada página. O bloco
`<nav id="resumos-novos">` mantém o contrato usado pelo pipeline de resumos:
novos PRs acrescentam apenas um `<li>` na categoria correspondente.

## Lote histórico de outubro de 2026

O arquivo [`BACKFILL_2026-10.md`](BACKFILL_2026-10.md) concilia os 66 vídeos
distintos encontrados nos jobs concluídos do pipeline: páginas novas, páginas
antigas reescritas, página preservada, página bloqueada e vídeos fora do escopo.

Os resumos são **rascunhos automatizados**. Cada ponto tem um link de tempo; a
revisão humana deve ouvir o trecho, conferir nomes, números e atribuição de falas
antes do merge. O acervo não faz merge automático de PRs.

## Endereços antigos

As páginas antes ficavam na raiz (`wsf001.html`, `wsf306_Especial.html`). O
`404.html` redireciona esses endereços para as novas pastas, preservando links
já compartilhados.
