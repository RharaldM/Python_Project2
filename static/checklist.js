document.addEventListener('DOMContentLoaded', function() {
    const checklistContainer = document.getElementById('checklist-container');
    const addSubtaskBtn = document.getElementById('add-subtask-btn');

    if (!checklistContainer || !addSubtaskBtn) return;

    let subtaskCounter = 0;

    function createChecklistItem() {
        subtaskCounter++;
        const subtaskDiv = document.createElement('div');
        subtaskDiv.className = 'input-group mb-2';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control form-control-sm';
        input.name = `subtask_description_${subtaskCounter}`;
        input.placeholder = `Subtarefa ${subtaskCounter}`;
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-outline-danger btn-sm';
        removeBtn.textContent = 'Remover';
        removeBtn.onclick = function() {
            subtaskDiv.remove();
        };

        subtaskDiv.appendChild(input);
        subtaskDiv.appendChild(removeBtn);
        checklistContainer.appendChild(subtaskDiv);
        input.focus();
    }

    addSubtaskBtn.addEventListener('click', createChecklistItem);
});