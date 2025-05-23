document.addEventListener('DOMContentLoaded', function() {
    const checklistContainer = document.getElementById('checklist-container');
    const addSubtaskBtn = document.getElementById('add-subtask');

    if (!checklistContainer || !addSubtaskBtn) return;

    function createChecklistItem(description = '', completed = false) {
        const div = document.createElement('div');
        div.className = 'input-group mb-2 checklist-item';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control';
        input.name = 'subtask_description[]';
        input.placeholder = 'Digite uma subtarefa';
        input.required = true;
        input.value = description;

        div.appendChild(input);

        // Opcional: adicionar checkbox para marcar como concluída na edição
        if (window.location.href.includes('edit_task')) {
            const groupText = document.createElement('div');
            groupText.className = 'input-group-text';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input mt-0';
            checkbox.name = 'subtask_completed[]';
            checkbox.value = checklistContainer.childElementCount;
            if (completed) checkbox.checked = true;
            groupText.appendChild(checkbox);
            div.appendChild(groupText);
        }

        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-outline-danger remove-subtask';
        removeBtn.innerHTML = '&times;';
        removeBtn.onclick = function() {
            div.remove();
        };
        div.appendChild(removeBtn);

        return div;
    }

    addSubtaskBtn.onclick = function() {
        checklistContainer.appendChild(createChecklistItem());
    };

    // Eventos para remover já são delegados nos botões

    // Se não estamos editando, não há subtarefas já carregadas
});