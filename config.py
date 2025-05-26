from flask_sqlalchemy import SQLAlchemy
from datetime import datetime as dt
from enum import Enum
from sqlalchemy import ForeignKey, Table
from sqlalchemy.orm import relationship
import os
from datetime import datetime, timedelta
db = SQLAlchemy()

class Priority(Enum):
    BAIXA = 'BAIXA'
    MEDIA = 'MEDIA'
    ALTA = 'ALTA'
    URGENTE = 'URGENTE'

# Definir a tabela associativa dentro da classe Config
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'supersecretkey'
    
    # Configurações do banco de dados
    SQLALCHEMY_DATABASE_URI = 'sqlite://'  # Usando SQLite em memória
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações do e-mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@taskmanager.com'
    
    # Configurações do log
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Configurações de cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Definir a tabela associativa aqui
    task_categories = Table('task_categories', db.metadata,
        db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
        db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
    )

# Agora podemos definir os modelos
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=dt.now)
    tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Enum(Priority), nullable=False, default=Priority.MEDIA)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=dt.now)
    due_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    categories = db.relationship('Category', secondary=Config.task_categories, backref=db.backref('tasks', lazy=True))
    subtasks = db.relationship('SubTask', backref='task', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=dt.now)

class SubTask(db.Model):
    __tablename__ = 'subtasks'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=dt.now)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)