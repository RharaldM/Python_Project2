document.addEventListener('DOMContentLoaded', function() {
    const categoryInput = document.getElementById('category-input');
    const addCategoryBtn = document.getElementById('add-category-btn');
    const selectedCategoriesList = document.getElementById('selected-categories-list');
    const hiddenCategoriesInput = document.getElementById('hidden-categories-input');

    if (!categoryInput || !addCategoryBtn || !selectedCategoriesList || !hiddenCategoriesInput) {
        return;
    }

    let selectedCategories = new Set();

    function updateHiddenInput() {
        hiddenCategoriesInput.value = Array.from(selectedCategories).join(',');
    }

    function addCategoryToDisplay(categoryName) {
        const trimmedCategoryName = categoryName.trim();
        if (!trimmedCategoryName || selectedCategories.has(trimmedCategoryName)) {
            return;
        }
        selectedCategories.add(trimmedCategoryName);

        const tag = document.createElement('span');
        tag.classList.add('category-tag', 'badge', 'text-bg-info', 'me-1', 'd-flex', 'align-items-center');
        tag.style.fontWeight = "bold";
        tag.style.fontSize = "1.15em";
        tag.style.backgroundColor = "#00d0ff";

        const textSpan = document.createElement('span');
        textSpan.textContent = trimmedCategoryName;

        const removeBtn = document.createElement('button');
        removeBtn.classList.add('btn-close', 'btn-close-white', 'ms-2');
        removeBtn.setAttribute('type', 'button');
        removeBtn.setAttribute('aria-label', 'Remover');
        removeBtn.style.filter = "none";
        removeBtn.style.opacity = "1";

        removeBtn.addEventListener('click', function() {
            removeCategory(trimmedCategoryName);
        });

        tag.appendChild(textSpan);
        tag.appendChild(removeBtn);
        selectedCategoriesList.appendChild(tag);
        updateHiddenInput();
    }

    function removeCategory(categoryName) {
        selectedCategories.delete(categoryName);
        const tags = selectedCategoriesList.querySelectorAll('.category-tag');
        tags.forEach(tag => {
            if (tag.firstChild.textContent === categoryName) {
                tag.remove();
            }
        });
        updateHiddenInput();
    }

    addCategoryBtn.addEventListener('click', function() {
        const inputValue = categoryInput.value.trim();
        if (inputValue) {
            const categoriesToAdd = inputValue.split(',').map(cat => cat.trim()).filter(cat => cat);
            categoriesToAdd.forEach(cat => addCategoryToDisplay(cat));
            categoryInput.value = '';
        }
    });

    categoryInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            const inputValue = categoryInput.value.trim();
            if (inputValue) {
                const categoriesToAdd = inputValue.split(',').map(cat => cat.trim()).filter(cat => cat);
                categoriesToAdd.forEach(cat => addCategoryToDisplay(cat));
                categoryInput.value = '';
            }
        }
    });
});