let checklistInitialized = false;

function initializeChecklist() {
    if (checklistInitialized) return;
    checklistInitialized = true;

    const checklistContainer = document.getElementById('checklist-container');
    const addSubtaskBtn = document.querySelector('[id^="add-subtask"]');

    if (!checklistContainer || !addSubtaskBtn) {
        console.error('Checklist container or add button not found');
        return;
    }

    // Função para adicionar um campo de subtarefa
    function addSubtask(description = '') {
        const subtaskDiv = document.createElement('div');
        subtaskDiv.className = 'input-group mb-2 checklist-item';
        
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control';
        input.name = 'subtask_description[]';
        input.placeholder = 'Digite uma subtarefa';
        input.value = description;
        input.required = true;
        
        // Adiciona checkbox se estiver em modo de edição
        const isEditMode = document.querySelector('.form-check-input');
        if (isEditMode) {
            const checkboxDiv = document.createElement('div');
            checkboxDiv.className = 'input-group-text';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input mt-0';
            checkbox.name = 'subtask_completed[]';
            checkboxDiv.appendChild(checkbox);
            subtaskDiv.appendChild(checkboxDiv);
        }
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-outline-danger remove-subtask btn-sm';
        removeBtn.innerHTML = '×';
        removeBtn.setAttribute('aria-label', 'Remover subtarefa');
        
        // Adiciona animação de fade-out
        removeBtn.addEventListener('click', function() {
            const subtaskDiv = this.closest('.checklist-item');
            subtaskDiv.classList.add('fade-out');
            
            // Aguarda a animação terminar antes de remover o elemento
            setTimeout(() => {
                subtaskDiv.classList.add('fade-out-leave');
                subtaskDiv.remove();
            }, 300);
        });

        subtaskDiv.appendChild(input);
        subtaskDiv.appendChild(removeBtn);
        checklistContainer.appendChild(subtaskDiv);
    }

    // Adiciona nova subtarefa ao clicar no botão
    addSubtaskBtn.addEventListener('click', function() {
        addSubtask();
    });

    // Configura remoção de subtarefas existentes
    document.querySelectorAll('.remove-subtask').forEach(button => {
        button.addEventListener('click', function() {
            const subtaskDiv = this.closest('.checklist-item');
            subtaskDiv.classList.add('fade-out');
            
            // Aguarda a animação terminar antes de remover o elemento
            setTimeout(() => {
                subtaskDiv.classList.add('fade-out-leave');
                subtaskDiv.remove();
            }, 300);
        });
    });

    // Validação antes do envio do formulário
    const taskForm = document.getElementById('task-form');
    if (taskForm) {
        taskForm.addEventListener('submit', function(event) {
            const subtaskInputs = document.querySelectorAll('input[name="subtask_description[]"]');
            subtaskInputs.forEach(input => {
                if (!input.value.trim()) {
                    input.parentNode.remove(); // Remove campos vazios
                }
            });
        }, { once: true });
    }
}

// Inicializa quando o DOM estiver carregado
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeChecklist);
} else {
    initializeChecklist();
}