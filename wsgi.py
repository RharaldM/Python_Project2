import os
import logging
from app import create_app
from config import Config
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

# Criar e inicializar a aplicação
application = create_app()

# Garantir que o banco de dados seja criado
with application.app_context():
    from models import db
    db.create_all()

if __name__ == '__main__':
    application.run()