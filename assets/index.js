(() => {
    "use strict";

    const input = document.querySelector("#busca");
    const clear = document.querySelector("#limpar");
    const result = document.querySelector("#resultado");
    const empty = document.querySelector("#vazio");
    const buttons = Array.from(document.querySelectorAll(".filter"));
    const sections = Array.from(document.querySelectorAll(".catalog-section"));
    const cards = Array.from(document.querySelectorAll("#resumos-novos .catalog-section > ul > li"));

    if (!input || !result || !empty || !cards.length) return;

    let active = "all";

    const normalize = (value) => value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLocaleLowerCase("pt-BR")
        .trim();

    const plural = (n, one, many) => `${n} ${n === 1 ? one : many}`;

    const updateTotals = () => {
        const totals = { total: cards.length, wsf: 0, rc: 0, especiais: 0 };
        cards.forEach((card) => {
            const section = card.closest(".catalog-section");
            if (section) totals[section.dataset.category] += 1;
        });
        Object.entries(totals).forEach(([key, value]) => {
            const node = document.querySelector(`[data-stat="${key}"]`);
            if (node) node.textContent = String(value);
        });
        sections.forEach((section) => {
            const node = section.querySelector(`[data-count="${section.dataset.category}"]`);
            const count = totals[section.dataset.category] || 0;
            if (node) node.textContent = plural(count, "resumo", "resumos");
        });
    };

    const apply = () => {
        const query = normalize(input.value);
        const visibleBySection = new Map();
        let visible = 0;

        cards.forEach((card) => {
            const section = card.closest(".catalog-section");
            const category = section ? section.dataset.category : "";
            const haystack = normalize(card.dataset.search || card.textContent || "");
            const matchesCategory = active === "all" || category === active;
            const matchesQuery = !query || haystack.includes(query);
            const show = matchesCategory && matchesQuery;
            card.hidden = !show;
            if (show) {
                visible += 1;
                visibleBySection.set(category, (visibleBySection.get(category) || 0) + 1);
            }
        });

        sections.forEach((section) => {
            const category = section.dataset.category;
            const matchesCategory = active === "all" || category === active;
            section.hidden = !matchesCategory || !(visibleBySection.get(category) || 0);
        });

        empty.hidden = visible !== 0;
        clear.hidden = !input.value;
        result.textContent = (query || active !== "all")
            ? `Mostrando ${visible} de ${plural(cards.length, "resumo", "resumos")}.`
            : `${plural(cards.length, "resumo", "resumos")} no acervo.`;
    };

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            active = button.dataset.filter || "all";
            buttons.forEach((item) => {
                const selected = item === button;
                item.classList.toggle("is-active", selected);
                item.setAttribute("aria-pressed", String(selected));
            });
            apply();
        });
    });

    input.addEventListener("input", apply);
    input.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            input.value = "";
            apply();
            input.blur();
        }
    });

    if (clear) {
        clear.addEventListener("click", () => {
            input.value = "";
            active = "all";
            buttons.forEach((button) => {
                const selected = button.dataset.filter === "all";
                button.classList.toggle("is-active", selected);
                button.setAttribute("aria-pressed", String(selected));
            });
            apply();
            input.focus();
        });
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "/" && document.activeElement !== input
            && !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName)) {
            event.preventDefault();
            input.focus();
        }
    });

    updateTotals();
    apply();
})();
