document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('toggle-dark-mode');
    const body = document.body;

    // Função para atualizar cores dos gráficos
    function updateChartColors(theme) {
        if (typeof Chart === 'undefined' || typeof Chart.helpers === 'undefined' || typeof Chart.instances === 'undefined') {
            // console.warn('Chart.js ou suas instâncias não estão disponíveis. Cores dos gráficos não serão atualizadas.');
            return;
        }

        const isDarkMode = theme === 'dark';
        const chartTextColor = isDarkMode ? '#f8f9fa' : '#212529'; // Cores típicas do Bootstrap
        const chartGridColor = isDarkMode ? '#495057' : '#dee2e6'; // Cores típicas do Bootstrap

        // Atualizar cores globais do Chart.js para novos gráficos
        Chart.defaults.color = chartTextColor;
        Chart.defaults.borderColor = chartGridColor;

        // Atualizar gráficos existentes
        Chart.helpers.each(Chart.instances, function (instance) {
            instance.options.scales = instance.options.scales || {};
            
            if (instance.options.scales.x) {
                instance.options.scales.x.ticks = instance.options.scales.x.ticks || {};
                instance.options.scales.x.ticks.color = chartTextColor;
                instance.options.scales.x.grid = instance.options.scales.x.grid || {};
                instance.options.scales.x.grid.color = chartGridColor;
            }

            if (instance.options.scales.y) {
                instance.options.scales.y.ticks = instance.options.scales.y.ticks || {};
                instance.options.scales.y.ticks.color = chartTextColor;
                instance.options.scales.y.grid = instance.options.scales.y.grid || {};
                instance.options.scales.y.grid.color = chartGridColor;
            }

            instance.options.plugins = instance.options.plugins || {};
            if (instance.options.plugins.legend) {
                instance.options.plugins.legend.labels = instance.options.plugins.legend.labels || {};
                instance.options.plugins.legend.labels.color = chartTextColor;
            }

            if (instance.options.plugins.title) {
                instance.options.plugins.title.color = chartTextColor;
            }

            instance.update('none'); // 'none' para evitar re-animação se não for desejado
        });
    }

    // Só executa a lógica de tema se o botão e o body existirem
    if (btn && body) {
        // Determina o tema inicial
        let preferredTheme = localStorage.getItem('darkMode'); // 'enabled' ou 'disabled'
        let currentTheme = (preferredTheme === 'enabled') ? 'dark' : 'light';

        // Aplica o tema inicial ao body
        body.setAttribute('data-bs-theme', currentTheme);

        // Atualiza o ícone e título do botão
        if (btn.querySelector('#theme-icon')) { // Se o span com id #theme-icon existir
            btn.querySelector('#theme-icon').className = (currentTheme === 'dark') ? 'bi bi-sun' : 'bi bi-moon';
        } else { // Fallback se o span não tiver id, mas for o único filho
            btn.innerHTML = (currentTheme === 'dark') ? '<span class="bi bi-sun"></span>' : '<span class="bi bi-moon"></span>';
        }
        btn.title = (currentTheme === 'dark') ? 'Alternar para modo claro' : 'Alternar para modo escuro';
        
        // Atualiza cores dos gráficos no carregamento inicial
        updateChartColors(currentTheme);

        // Listener para o clique no botão
        btn.addEventListener('click', function () {
            const oldTheme = body.getAttribute('data-bs-theme');
            const newTheme = (oldTheme === 'dark') ? 'light' : 'dark';

            body.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('darkMode', (newTheme === 'dark') ? 'enabled' : 'disabled');
            
            if (btn.querySelector('#theme-icon')) {
                btn.querySelector('#theme-icon').className = (newTheme === 'dark') ? 'bi bi-sun' : 'bi bi-moon';
            } else {
                btn.innerHTML = (newTheme === 'dark') ? '<span class="bi bi-sun"></span>' : '<span class="bi bi-moon"></span>';
            }
            btn.title = (newTheme === 'dark') ? 'Alternar para modo claro' : 'Alternar para modo escuro';
            
            updateChartColors(newTheme);
            // console.log('Tema alterado para:', newTheme);
        });
    } else {
        if (!btn) console.warn("Botão 'toggle-dark-mode' não encontrado.");
        if (!body) console.warn("Elemento <body> não encontrado.");
    }

    // Inicializa tooltips do Bootstrap
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Tooltip === 'function') {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
});