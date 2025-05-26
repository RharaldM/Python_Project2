from flask import Flask, session, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from models import db, User, Task
import logging
import os
import pandas as pd
from io import BytesIO
from sqlalchemy.orm import joinedload
from routes import routes
from models import db, Task, User

# Definir o diretório base do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Criar diretórios necessários
os.makedirs(os.path.join(BASE_DIR, 'instance', 'logs'), exist_ok=True)

# Configurar logging
log_file_path = os.path.join(BASE_DIR, 'instance', 'logs', 'app.log')

# Criar o diretório pai do arquivo de log se não existir
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Função auxiliar para carregar tarefas com categorias
def get_tasks_with_categories(user_id):
    """Retorna as tarefas com as categorias carregadas."""
    return Task.query.filter_by(user_id=user_id).options(
        joinedload(Task.categories)
    ).all()

# Imports for export
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd

login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Criar as tabelas do banco de dados
    with app.app_context():
        db.create_all()

    # Registrar blueprints
    app.register_blueprint(routes)

    # Configurar login manager
    login_manager.login_view = 'routes.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/export_excel')
    def export_excel():
        if 'user_id' not in session:
            return redirect(url_for('routes.login'))
            
        tasks = Task.query.filter_by(user_id=session['user_id']).all()
        
        # Criar DataFrame
        df = pd.DataFrame([
            {
                'Título': task.title,
                'Descrição': task.description,
                'Data de Vencimento': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
                'Prioridade': task.priority.name if task.priority else '',
                'Status': 'Concluída' if task.completed else 'Pendente',
                'Criado em': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Atualizado em': task.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for task in tasks
        ])
        
        # Criar buffer
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Tarefas', index=False)
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name="tarefas.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)