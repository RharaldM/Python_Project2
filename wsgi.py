from app import create_app
from config import Config

application = create_app()

# Garantir que o banco de dados seja criado
with application.app_context():
    from models import db
    db.create_all()

if __name__ == '__main__':
    application.run()