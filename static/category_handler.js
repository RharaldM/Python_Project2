document.addEventListener('DOMContentLoaded', function() {
    // Define all required elements
    const categoryInput = document.getElementById('category-input');
    const addCategoryBtn = document.getElementById('add-category-btn');
    const selectedCategoriesList = document.getElementById('selected-categories-list');
    const hiddenCategoriesInput = document.getElementById('hidden-categories-input');
    
    // Debug log to check if elements exist
    console.log('Elements found:', {
        categoryInput: !!categoryInput,
        addCategoryBtn: !!addCategoryBtn,
        selectedCategoriesList: !!selectedCategoriesList,
        hiddenCategoriesInput: !!hiddenCategoriesInput
    });

    // Early return if required elements are missing
    if (!categoryInput || !addCategoryBtn || !selectedCategoriesList || !hiddenCategoriesInput) {
        console.error('Required elements not found');
        return;
    }

    // Set to store unique categories
    let selectedCategories = new Set();

    // Updates hidden input with current categories
    function updateHiddenInput() {
        hiddenCategoriesInput.value = Array.from(selectedCategories).join(',');
    }

    // Adds a category to display
    function addCategoryToDisplay(categoryName) {
        const trimmedCategoryName = categoryName.trim();
        if (!trimmedCategoryName || selectedCategories.has(trimmedCategoryName)) {
            return;
        }

        // Add to set
        selectedCategories.add(trimmedCategoryName);

        // Create badge with explicit styles
        const tag = document.createElement('span');
        tag.className = 'category-tag badge bg-info text-white';
        tag.style.display = 'inline-flex';
        tag.style.alignItems = 'center';
        
        // Add category text
        const textNode = document.createTextNode(trimmedCategoryName);
        tag.appendChild(textNode);

        // Create remove button com estilos explícitos
        const removeBtn = document.createElement('button');
        removeBtn.className = 'btn-close btn-close-white';
        removeBtn.type = 'button';
        removeBtn.setAttribute('aria-label', 'Remover');
        // Estilos inline para garantir
        removeBtn.style.cssText = `
            display: inline-block !important;
            width: 0.8em !important;
            height: 0.8em !important;
            margin-left: 0.5em !important;
            visibility: visible !important;
            opacity: 0.8 !important;
        `;
        
        // Add click handler to remove button
        removeBtn.addEventListener('click', () => removeCategory(trimmedCategoryName));
        
        // Add button to badge
        tag.appendChild(removeBtn);
        
        // Add badge to list
        selectedCategoriesList.appendChild(tag);
        
        // Update hidden input
        updateHiddenInput();
    }

    // Removes a category
    function removeCategory(categoryName) {
        selectedCategories.delete(categoryName);
        const tags = selectedCategoriesList.querySelectorAll('.category-tag');
        tags.forEach(tag => {
            if (tag.firstChild?.nodeType === Node.TEXT_NODE && 
                tag.firstChild.textContent === categoryName) {
                tag.remove();
            }
        });
        updateHiddenInput();
    }

    // Add category button click handler
    addCategoryBtn.addEventListener('click', () => {
        const inputValue = categoryInput.value.trim();
        if (inputValue) {
            const categories = inputValue.split(',')
                .map(cat => cat.trim())
                .filter(cat => cat);
            categories.forEach(addCategoryToDisplay);
            categoryInput.value = '';
        }
    });

    // Enter key handler
    categoryInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            const inputValue = categoryInput.value.trim();
            if (inputValue) {
                const categories = inputValue.split(',')
                    .map(cat => cat.trim())
                    .filter(cat => cat);
                categories.forEach(addCategoryToDisplay);
                categoryInput.value = '';
            }
        }
    });

    // Initialize categories from data attribute if available
    try {
        const initialCategoriesDiv = document.getElementById('initial-categories-data');
        if (initialCategoriesDiv) {
            console.log('Found initial categories div');
            let categoriesData = initialCategoriesDiv.dataset.categories;
            console.log('Categories data:', categoriesData);
            
            if (!categoriesData || categoriesData.trim() === '') {
                console.log('No categories data, using empty array');
                categoriesData = '[]';
            }
            
            const initialCategories = JSON.parse(categoriesData);
            console.log('Parsed categories:', initialCategories);
            
            if (Array.isArray(initialCategories)) {
                initialCategories.forEach(addCategoryToDisplay);
            }
        }
    } catch (error) {
        console.error('Error initializing categories:', error);
    }
});