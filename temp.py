from models import Task, Category, joinedload

def get_tasks_with_categories(user_id):
    """Retorna as tarefas com as categorias carregadas."""
    return Task.query.filter_by(user_id=user_id).options(joinedload(Task.categories)).all()
