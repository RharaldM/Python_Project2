document.addEventListener('DOMContentLoaded', function() {
    const categoryInput = document.getElementById('category-input');
    const addCategoryBtn = document.getElementById('add-category-btn');
    const selectedCategoriesList = document.getElementById('selected-categories-list');
    const hiddenCategoriesInput = document.getElementById('hidden-categories-input');

    if (!categoryInput || !addCategoryBtn || !selectedCategoriesList || !hiddenCategoriesInput) {
        console.error('Required elements not found');
        return;
    }

    let selectedCategories = new Set();

    // Initialize from existing categories if editing
    const initialCategoriesData = document.getElementById('initial-categories-data');
    if (initialCategoriesData) {
        try {
            const initialCategories = JSON.parse(initialCategoriesData.dataset.categories);
            console.log('Initial categories:', initialCategories);
            initialCategories.forEach(category => addCategoryToDisplay(category));
        } catch (e) {
            console.error('Error parsing initial categories:', e);
        }
    }

    function updateHiddenInput() {
        hiddenCategoriesInput.value = Array.from(selectedCategories).join(',');
    }

    function addCategoryToDisplay(categoryName) {
        console.log('Adding category:', categoryName);
        const trimmedCategoryName = categoryName.trim();
        if (!trimmedCategoryName || selectedCategories.has(trimmedCategoryName)) {
            console.log('Category already exists or empty:', trimmedCategoryName);
            return;
        }
        selectedCategories.add(trimmedCategoryName);

        const tag = document.createElement('span');
        tag.classList.add('category-tag', 'badge', 'bg-info', 'text-white', 'me-2', 'mb-2', 'd-inline-flex', 'align-items-center');

        const nameSpan = document.createElement('span');
        nameSpan.textContent = trimmedCategoryName;
        nameSpan.style.marginRight = '5px';
        tag.appendChild(nameSpan);

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn-close btn-close-white';
        removeBtn.style.fontSize = '0.8em';
        removeBtn.style.marginLeft = '5px';
        removeBtn.setAttribute('aria-label', 'Remove');
        removeBtn.addEventListener('click', () => {
            console.log('Removing category:', trimmedCategoryName);
            removeCategory(trimmedCategoryName);
        });

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