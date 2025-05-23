document.addEventListener('DOMContentLoaded', function() {
    const categoryInput = document.getElementById('category-input');
    const addCategoryBtn = document.getElementById('add-category-btn');
    const selectedCategoriesList = document.getElementById('selected-categories-list');
    const hiddenCategoriesInput = document.getElementById('hidden-categories-input');

    if (!categoryInput || !addCategoryBtn || !selectedCategoriesList || !hiddenCategoriesInput) {
        // Se os elementos não existirem (ex: em páginas que não usam categorias), não faça nada.
        return;
    }

    let selectedCategories = new Set(); // Usar Set para garantir unicidade

    // Função para atualizar o campo hidden com as categorias selecionadas
    function updateHiddenInput() {
        hiddenCategoriesInput.value = Array.from(selectedCategories).join(',');
    }

    // Função para adicionar uma categoria ao display e ao Set
    function addCategoryToDisplay(categoryName) {
        const trimmedCategoryName = categoryName.trim();
        if (!trimmedCategoryName || selectedCategories.has(trimmedCategoryName)) {
            return; // Não adicionar vazios ou duplicatas
        }
        selectedCategories.add(trimmedCategoryName);

        const tag = document.createElement('span');
        tag.classList.add('category-tag', 'badge', 'text-bg-info', 'me-1'); // Adiciona classes Bootstrap
        tag.textContent = trimmedCategoryName;

        const removeBtn = document.createElement('button');
        removeBtn.classList.add('btn-close', 'btn-close-white', 'ms-2'); // Bootstrap close button
        removeBtn.setAttribute('type', 'button');
        removeBtn.setAttribute('aria-label', 'Remover');
        removeBtn.addEventListener('click', function() {
            removeCategory(trimmedCategoryName);
        });

        tag.appendChild(removeBtn);
        selectedCategoriesList.appendChild(tag);
        updateHiddenInput(); // Chama aqui para atualizar o input escondido
    }

    // Função para remover uma categoria do display e do Set
    function removeCategory(categoryName) {
        selectedCategories.delete(categoryName);
        const tags = selectedCategoriesList.querySelectorAll('.category-tag');
        tags.forEach(tag => {
            if (tag.firstChild.textContent === categoryName) {
                tag.remove();
            }
        });
        updateHiddenInput(); // Chama aqui também
    }

    // Carregar categorias existentes na edição de tarefas
    const initialCategoriesElement = document.getElementById('initial-categories-data');
    if (initialCategoriesElement) {
        try {
            const initialCategories = JSON.parse(initialCategoriesElement.dataset.categories);
            initialCategories.forEach(cat => addCategoryToDisplay(cat));
        } catch (e) {
            console.error("Erro ao parsear categorias iniciais:", e);
        }
    }


    // Adicionar categoria ao clicar no botão
    addCategoryBtn.addEventListener('click', function() {
        const inputValue = categoryInput.value.trim();
        if (inputValue) {
            // Suporta múltiplas categorias separadas por vírgula na entrada
            const categoriesToAdd = inputValue.split(',').map(cat => cat.trim()).filter(cat => cat);
            categoriesToAdd.forEach(cat => addCategoryToDisplay(cat));
            categoryInput.value = ''; // Limpa o input
        }
    });

    // Adicionar categoria ao pressionar Enter no input
    categoryInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault(); // Evita o envio do formulário
            const inputValue = categoryInput.value.trim();
            if (inputValue) {
                 const categoriesToAdd = inputValue.split(',').map(cat => cat.trim()).filter(cat => cat);
                 categoriesToAdd.forEach(cat => addCategoryToDisplay(cat));
                categoryInput.value = '';
            }
        }
    });
});