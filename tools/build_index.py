#!/usr/bin/env python3
"""Regenera o índice do acervo a partir das páginas em wsf/, rc/ e especiais/.

O bloco <nav id="resumos-novos"> mantém o contrato usado pelo pipeline de
resumos: cada categoria tem um <h3> e uma <ul> próprios, para que um novo PR
acrescente apenas um <li> sem reescrever o restante do índice.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATEGORY_ORDER = ("wsf", "rc", "especiais")
LABELS = {
    "wsf": "Weintraub sem Filtro",
    "rc": "Raiz Cristã",
    "especiais": "Especiais",
}
TITLE_BLOCK = re.compile(r"<li>\s*Title:\s*(.*?)</li>", re.I | re.S)
TITLE_H1 = re.compile(r'<h1[^>]*id=["\']Title["\'][^>]*>(.*?)</h1>', re.I | re.S)
VIDEO = re.compile(r"(?:youtube\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})")
HEADING = re.compile(r"<h([1-4])[^>]*>(.*?)</h\1>", re.I | re.S)
PARAGRAPH = re.compile(r"<p[^>]*>(.*?)</p>", re.I | re.S)
GENERIC_HEADINGS = {
    "metadata",
    "notes",
    "tempos do video",
    "tempos do vídeo",
    "summary",
    "resumo",
    "smart summary",
    "mindmap",
    "linha do tempo",
    "destaques",
    "conclusão",
    "conclusao",
    "análise e resumo do conteúdo",
    "analise e resumo do conteudo",
    "análise detalhada",
    "analise detalhada",
    "análise e síntese do conteúdo",
    "analise e sintese do conteudo",
    "listas de destaques e conclusões",
    "listas de destaques e conclusoes",
}
GENERIC_PREFIXES = (
    "metadata",
    "notes",
    "tempos do",
    "summary",
    "resumo",
    "smart summary",
    "mindmap",
    "linha do tempo",
    "destaques",
    "principais",
    "tabela",
    "conclus",
    "considera",
    "insights",
    "análise e resumo",
    "analise e resumo",
)
MONTHS = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


@dataclass(frozen=True)
class Entry:
    category: str
    path: str
    title: str
    topic: str
    video_id: str | None
    episode: int | None
    day: date | None

    @property
    def kicker(self) -> str:
        if self.category == "rc":
            if self.day:
                return f"Raiz Cristã · {self.day.day:02d} {MONTHS[self.day.month - 1]} {self.day.year}"
            return "Raiz Cristã"
        if self.category == "especiais":
            return "Especial"
        if self.episode is not None:
            return f"WSF #{self.episode:03d}"
        return "WSF"


def clean(fragment: str) -> str:
    """Converte HTML simples em texto legível para os cartões do índice."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", fragment or ""))
    return " ".join(text.split())


def title_of(page: str, episode: int | None) -> str:
    match = TITLE_BLOCK.search(page) or TITLE_H1.search(page)
    if match:
        title = clean(match.group(1))
        if title:
            return title
    return f"WSF #{episode:03d}" if episode is not None else "Resumo"


def topic_of(page: str, title: str) -> str:
    for _, raw in HEADING.findall(page):
        text = clean(raw)
        folded = text.casefold()
        if (len(text) < 12 or not text or folded in GENERIC_HEADINGS
                or folded.startswith(GENERIC_PREFIXES) or folded == title.casefold()):
            continue
        return text[:180]
    meta_prefixes = (
        "url:", "title:", "este é um resumo", "este resumo", "este vídeo",
        "este video", "o vídeo", "o video", "nesta live", "a live",
    )
    for raw in PARAGRAPH.findall(page):
        text = re.sub(r"^\[[^\]]+\]\s*", "", clean(raw))
        text = re.sub(r"^[#*\s]+", "", text)
        if len(text) >= 40 and not text.casefold().startswith(meta_prefixes):
            return text[:180]
    return ""


def parse(page_path: Path) -> Entry:
    page = page_path.read_text(encoding="utf-8")
    category = page_path.parent.name
    name = page_path.name
    episode_match = re.search(r"wsf(\d{3,4})", name, re.I)
    episode = int(episode_match.group(1)) if episode_match else None
    title = title_of(page, episode)
    video = VIDEO.search(page)
    day = None
    if category == "rc":
        date_match = re.match(r"(\d{4})-(\d{2})-(\d{2})-", name)
        if date_match:
            try:
                day = date.fromisoformat("-".join(date_match.groups()))
            except ValueError:
                day = None
    return Entry(
        category=category,
        path=page_path.relative_to(ROOT).as_posix(),
        title=title,
        topic=topic_of(page, title),
        video_id=video.group(1) if video else None,
        episode=episode,
        day=day,
    )


def card(entry: Entry) -> str:
    search = html.escape(" ".join((entry.kicker, entry.title, entry.topic)).casefold(), quote=True)
    topic = f'\n                    <span class="card-topic">{html.escape(entry.topic)}</span>' if entry.topic else ""
    return (
        '            <li class="summary-card" data-search="' + search + '">\n'
        '                <a class="card-link" href="' + html.escape(entry.path, quote=True) + '">\n'
        '                    <span class="card-kicker">' + html.escape(entry.kicker) + '</span>\n'
        '                    <span class="card-title">' + html.escape(entry.title) + '</span>' + topic + '\n'
        '                    <span class="card-arrow" aria-hidden="true">→</span>\n'
        '                </a>\n'
        '            </li>'
    )


def section(category: str, entries: list[Entry]) -> str:
    cards = "\n".join(card(entry) for entry in entries)
    count = len(entries)
    word = "resumo" if count == 1 else "resumos"
    return (
        f'    <section class="catalog-section" id="{category}" data-category="{category}">\n'
        f'        <p class="section-count"><span data-count="{category}">{count} {word}</span></p>\n'
        f'        <h3>{LABELS[category]}</h3>\n'
        '        <ul>\n'
        f'{cards}\n'
        '        </ul>\n'
        '    </section>'
    )


def build() -> str:
    entries: list[Entry] = []
    for category in CATEGORY_ORDER:
        pages = sorted((ROOT / category).glob("*.html"))
        if not pages:
            raise SystemExit(f"Pasta sem páginas: {category}/")
        category_entries = [parse(path) for path in pages]
        if category == "wsf":
            category_entries.sort(key=lambda item: (item.episode is None, item.episode or 0))
        elif category == "rc":
            category_entries.sort(key=lambda item: (item.day is None, item.day or date.min), reverse=True)
        else:
            category_entries.sort(key=lambda item: (item.episode is None, item.episode or 0))
        entries.extend(category_entries)

    for entry in entries:
        if not entry.path.startswith(entry.category + "/") or not entry.path.endswith(".html"):
            raise SystemExit(f"Caminho inválido: {entry.path}")
    if len({entry.path for entry in entries}) != len(entries):
        raise SystemExit("Página duplicada no índice")

    counts = {category: sum(entry.category == category for entry in entries) for category in CATEGORY_ORDER}
    total = len(entries)
    sections = "\n\n".join(section(category, [entry for entry in entries if entry.category == category])
                            for category in CATEGORY_ORDER)
    stat_words = {"wsf": "WSF", "rc": "Raiz Cristã", "especiais": "Especiais"}
    stats = "\n".join(
        f'                <div><dt>{stat_words[category]}</dt><dd data-stat="{category}">{counts[category]}</dd></div>'
        for category in CATEGORY_ORDER
    )
    filters = "\n".join(
        f'                <button type="button" class="filter" data-filter="{category}" aria-pressed="false">{LABELS[category]}</button>'
        for category in CATEGORY_ORDER
    )
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#f4efe5">
    <meta name="description" content="Resumos temáticos das lives de Weintraub sem Filtro, Raiz Cristã e programas especiais.">
    <title>Resumos | WSF, Raiz Cristã e Especiais</title>
    <link rel="stylesheet" href="assets/style.css">
    <script defer src="assets/index.js"></script>
</head>
<body>
    <a class="skip-link" href="#acervo">Pular para o acervo</a>

    <header class="site-header">
        <a class="brand" href="index.html" aria-label="Resumos — início">
            <span class="brand-mark">WSF</span>
            <span class="brand-name">Resumos</span>
        </a>
        <div class="top-links">
            <a href="#wsf">WSF</a>
            <a href="#rc">Raiz Cristã</a>
            <a href="#especiais">Especiais</a>
        </div>
    </header>

    <main>
        <section class="hero" aria-labelledby="hero-title">
            <p class="eyebrow">Acervo editorial</p>
            <h1 id="hero-title">As lives,<br><em>organizadas.</em></h1>
            <p class="lede">Resumos temáticos com marcas de tempo para conferir cada passagem no vídeo original. Um arquivo para consultar, revisar e acompanhar os programas.</p>
            <dl class="stats">
                <div><dt>Total</dt><dd data-stat="total">{total}</dd></div>
{stats}
            </dl>
        </section>

        <section class="catalog" id="acervo" aria-labelledby="acervo-title">
            <div class="catalog-head">
                <div>
                    <p class="eyebrow">Navegue</p>
                    <h2 id="acervo-title">Acervo completo</h2>
                </div>
                <div class="search-wrap">
                    <label for="busca">Buscar no acervo</label>
                    <input id="busca" type="search" placeholder="Episódio, tema ou palavra-chave" autocomplete="off">
                    <button type="button" class="clear" id="limpar" hidden>Limpar</button>
                </div>
            </div>

            <div class="filters" role="group" aria-label="Filtrar por programa">
                <button type="button" class="filter is-active" data-filter="all" aria-pressed="true">Todos</button>
{filters}
            </div>

            <p class="result" id="resultado" role="status" aria-live="polite">Mostrando {total} resumos.</p>

            <nav id="resumos-novos" aria-label="Novos resumos">
{sections}
            </nav>

            <p class="empty" id="vazio" hidden>Nenhum resumo encontrado. Tente outro termo.</p>
        </section>
    </main>

    <footer class="site-footer">
        <p>Resumos do acervo <strong>WSF</strong>, <strong>Raiz Cristã</strong> e <strong>Especiais</strong>.</p>
        <p>Confira sempre o vídeo original antes de citar ou compartilhar um trecho.</p>
    </footer>
</body>
</html>
'''


if __name__ == "__main__":
    (ROOT / "index.html").write_text(build(), encoding="utf-8")
    print("index.html regenerado")
