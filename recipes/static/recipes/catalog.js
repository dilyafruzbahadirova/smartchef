"use strict";

document.addEventListener("DOMContentLoaded", function () {
    const dataElement = document.getElementById(
        "product-catalog-data"
    );

    const searchInput = document.getElementById(
        "catalog-search"
    );

    const selectedContainer = document.getElementById(
        "catalog-selected"
    );

    const countElement = document.getElementById(
        "catalog-count"
    );

    const clearButton = document.getElementById(
        "catalog-clear"
    );

    const emptySelection = document.getElementById(
        "catalog-empty-selection"
    );

    const noResults = document.getElementById(
        "catalog-no-results"
    );

    const productContainer = document.getElementById(
        "catalog-products"
    );

    if (
        !dataElement ||
        !searchInput ||
        !selectedContainer ||
        !countElement ||
        !clearButton ||
        !emptySelection ||
        !noResults ||
        !productContainer
    ) {
        return;
    }

    const catalog = JSON.parse(
        document.getElementById(
            "product-catalog-data"
        ).textContent
    );

    const language = catalog.language === "ru"
        ? "ru"
        : "kk";

    const products = Array.isArray(catalog.products)
        ? catalog.products
        : [];

    const productLookup = new Map();

    products.forEach(function (product) {
        productLookup.set(product.id, product);
    });

    const cards = Array.from(
        productContainer.querySelectorAll(
            ".product-card[data-product-id][data-category]"
        )
    );

    const categoryButtons = Array.from(
        document.querySelectorAll(
            ".category-button[data-category]"
        )
    );

    let activeCategory = "all";

    function normalize(value) {
        return String(value || "")
            .trim()
            .toLocaleLowerCase();
    }

    function getCheckbox(card) {
        return card.querySelector(
            'input[type="checkbox"][name="selected_products"]'
        );
    }

    function getSelectedCards() {
        return cards.filter(function (card) {
            const checkbox = getCheckbox(card);

            return checkbox !== null && checkbox.checked;
        });
    }

    function getProductName(product) {
        return product[language] || product.kk || product.ru || "";
    }

    function createSelectedTag(card) {
        const productId = card.dataset.productId;
        const product = productLookup.get(productId);

        if (!product) {
            return null;
        }

        const tag = document.createElement("span");
        tag.className = "selected-tag";

        const name = document.createElement("span");
        name.textContent = getProductName(product);

        const removeButton = document.createElement("button");
        removeButton.type = "button";
        removeButton.textContent = "×";

        const removeLabel = language === "ru"
            ? "Убрать "
            : "Алып тастау: ";

        removeButton.setAttribute(
            "aria-label",
            removeLabel + getProductName(product)
        );

        removeButton.addEventListener("click", function () {
            const checkbox = getCheckbox(card);

            if (checkbox) {
                checkbox.checked = false;

                checkbox.dispatchEvent(
                    new Event("change", {
                        bubbles: true
                    })
                );
            }
        });

        tag.appendChild(name);
        tag.appendChild(removeButton);

        return tag;
    }

    function updateSelection() {
        const selectedCards = getSelectedCards();

        selectedContainer.replaceChildren();

        selectedCards.forEach(function (card) {
            const tag = createSelectedTag(card);

            if (tag) {
                selectedContainer.appendChild(tag);
            }
        });

        countElement.textContent = String(
            selectedCards.length
        );

        emptySelection.hidden = selectedCards.length > 0;

        clearButton.disabled = selectedCards.length === 0;
    }

    function filterProducts() {
        const searchTerm = normalize(searchInput.value);

        let visibleCount = 0;

        cards.forEach(function (card) {
            const productId = card.dataset.productId;
            const product = productLookup.get(productId);

            if (!product) {
                card.hidden = true;
                return;
            }

            const categoryMatches =
                activeCategory === "all" ||
                product.category === activeCategory;

            const kazakhName = normalize(product.kk);
            const russianName = normalize(product.ru);

            const searchMatches =
                searchTerm === "" ||
                kazakhName.includes(searchTerm) ||
                russianName.includes(searchTerm);

            const shouldShow =
                categoryMatches && searchMatches;

            card.hidden = !shouldShow;

            if (shouldShow) {
                visibleCount += 1;
            }
        });

        noResults.hidden = visibleCount !== 0;
    }

    function setActiveCategory(category) {
        activeCategory = category;

        categoryButtons.forEach(function (button) {
            const isActive =
                button.dataset.category === activeCategory;

            button.classList.toggle(
                "active",
                isActive
            );

            button.setAttribute(
                "aria-pressed",
                isActive ? "true" : "false"
            );
        });

        filterProducts();
    }

    categoryButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            setActiveCategory(
                button.dataset.category || "all"
            );
        });
    });

    searchInput.addEventListener("input", function () {
        filterProducts();
    });

    cards.forEach(function (card) {
        const checkbox = getCheckbox(card);

        if (!checkbox) {
            return;
        }

        checkbox.addEventListener("change", function () {
            updateSelection();
        });
    });

    clearButton.addEventListener("click", function () {
        cards.forEach(function (card) {
            const checkbox = getCheckbox(card);

            if (checkbox) {
                checkbox.checked = false;
            }
        });

        updateSelection();
    });

    updateSelection();
    filterProducts();
});