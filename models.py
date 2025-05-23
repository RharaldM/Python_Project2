from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import datetime # Importado para o default do timestamp

db = SQLAlchemy()

# Tabela associativa para a relação muitos-para-muitos entre Task e Category
task_categories = db.Table('task_categories',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

# Definir um Enum para as prioridades
class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)  # Campo adicionado para recuperação de senha
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    categories = db.relationship('Category', secondary=task_categories,
                                 backref=db.backref('tasks', lazy='dynamic'))
    priority = db.Column(db.Enum(Priority), nullable=False, default=Priority.MEDIUM)
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now) # Adicionado timestamp
    updated_at = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now) # Adicionado timestamp de atualização

    # RELACIONAMENTO COM SUBTAREFAS
    subtasks = db.relationship('SubTask', backref='task', cascade='all, delete-orphan', lazy=True, order_by="SubTask.id")

    def __repr__(self):
        return f'<Task {self.title}>'

class SubTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)

    def __repr__(self):
        return f'<SubTask {self.description} - {"Concluída" if self.completed else "Pendente"}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'