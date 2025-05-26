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

    function updateHiddenInput() {
        hiddenCategoriesInput.value = Array.from(selectedCategories).join(',');
    }

    function addCategoryToDisplay(categoryName) {
        const trimmedCategory = categoryName.trim();
        if (!trimmedCategory || selectedCategories.has(trimmedCategory)) {
            return;
        }

        selectedCategories.add(trimmedCategory);
        
        const tag = document.createElement('span');
        tag.className = 'category-tag';
        
        const textSpan = document.createElement('span');
        textSpan.textContent = trimmedCategory;
        tag.appendChild(textSpan);
        
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'btn btn-sm btn-outline-danger ms-2';
        closeBtn.innerHTML = '×';
        
        closeBtn.addEventListener('click', function() {
            selectedCategories.delete(trimmedCategory);
            tag.remove();
            updateHiddenInput();
            categoryInput.focus();
        });
        
        tag.appendChild(closeBtn);
        selectedCategoriesList.appendChild(tag);
        updateHiddenInput();
        
        categoryInput.value = '';
        categoryInput.focus();
    }

    addCategoryBtn.addEventListener('click', function() {
        addCategoryToDisplay(categoryInput.value);
    });

    categoryInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            addCategoryToDisplay(this.value);
        }
    });

    const initialCategoriesData = document.getElementById('initial-categories-data');
    if (initialCategoriesData) {
        try {
            const initialCategories = JSON.parse(initialCategoriesData.dataset.categories);
            initialCategories.forEach(category => addCategoryToDisplay(category));
        } catch (e) {
            console.error('Error parsing initial categories:', e);
        }
    }
});