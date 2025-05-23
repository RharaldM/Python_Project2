document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('toggle-dark-mode');
    // Carrega preferência se houver
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        btn.innerHTML = '☀️';
        btn.title = 'Alternar para modo claro';
    }
    btn.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
        const enabled = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', enabled ? 'enabled' : 'disabled');
        btn.innerHTML = enabled ? '☀️' : '🌙';
        btn.title = enabled ? 'Alternar para modo claro' : 'Alternar para modo escuro';
    });
});