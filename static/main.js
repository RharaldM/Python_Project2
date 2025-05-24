document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('toggle-dark-mode');
    const alerts = document.querySelectorAll('.alert-dismissible');

    // Carrega preferência se houver
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        btn.innerHTML = '☀️';
        btn.title = 'Alternar para modo claro';
    }

    // Alternar tema
    btn.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
        const enabled = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', enabled ? 'enabled' : 'disabled');
        btn.innerHTML = enabled ? '☀️' : '🌙';
        btn.title = enabled ? 'Alternar para modo claro' : 'Alternar para modo escuro';
    });

    // Foco automático em alertas ao serem exibidos
    alerts.forEach(alert => {
        alert.addEventListener('transitionend', () => {
            alert.focus();
        });
    });
});