document.addEventListener('DOMContentLoaded', function() {
    // Inicializa todos os componentes do Bootstrap que dependem de JavaScript,
    // como dropdowns, tooltips, popovers, modais, etc.
    // bootstrap.bundle.min.js já faz isso automaticamente para a maioria dos componentes
    // que são ativados com data attributes (como data-bs-toggle="dropdown").

    // Se você tiver tooltips no seu HTML (elementos com data-bs-toggle="tooltip"),
    // eles precisam ser inicializados explicitamente assim:
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // O mesmo para popovers, se você os usar:
    // const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    // const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));

    // Este script é mais para inicializações específicas ou para adicionar
    // lógicas JavaScript globais do seu site que dependam do Bootstrap.
    // Para o seu problema original do dropdown, o bootstrap.bundle.min.js já deveria ser suficiente.
    // No entanto, ter este arquivo para futuras inicializações ou depurações é uma boa prática.
});