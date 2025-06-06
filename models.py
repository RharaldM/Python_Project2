from flask_sqlalchemy import SQLAlchemy
from datetime import datetime as dt
from enum import Enum
from sqlalchemy import ForeignKey, Table
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Priority(Enum):
    BAIXA = 'BAIXA'
    MEDIA = 'MEDIA'
    ALTA = 'ALTA'
    URGENTE = 'URGENTE'

# Definir a tabela associativa
task_categories = Table('task_categories', db.metadata,
    db.Column('task_id', db.Integer, db.ForeignKey('tasks.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

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
    categories = db.relationship('Category', secondary=task_categories, backref=db.backref('tasks', lazy=True))
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

    def __repr__(self):
        return f'<SubTask {self.description} - {"Concluída" if self.completed else "Pendente"}>'