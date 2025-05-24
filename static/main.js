document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('toggle-dark-mode');
    const alerts = document.querySelectorAll('.alert-dismissible');

    // Carrega preferência se houver
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        btn.innerHTML = '☀️';
        btn.title = 'Alternar para modo claro';
        console.log('Dark mode enabled on load');
    }

    // Alternar tema
    btn.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
        const enabled = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', enabled ? 'enabled' : 'disabled');
        btn.innerHTML = enabled ? '☀️' : '🌙';
        btn.title = enabled ? 'Alternar para modo claro' : 'Alternar para modo escuro';
        console.log('Dark mode toggled:', enabled);
    });

    // Foco automático em alertas ao serem exibidos
    alerts.forEach(alert => {
        alert.addEventListener('transitionend', () => {
            alert.focus();
            console.log('Alert focused:', alert);
        });
    });

    // Inicializa tooltips do Bootstrap
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
});