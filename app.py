from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
from models import db, User, Task, Category, Priority, SubTask
from werkzeug.security import generate_password_hash, check_password_hash
import os
from collections import defaultdict, Counter
import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
from functools import wraps
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import logging
import sys

def get_tasks_with_categories(user_id):
    """Retorna as tarefas com as categorias carregadas."""
    return Task.query.filter_by(user_id=user_id).options(joinedload(Task.categories)).all()

# Imports for export
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rharaldmoreirag@gmail.com'
app.config['MAIL_PASSWORD'] = 'czrc uxli kxet vtwc'
app.config['MAIL_DEFAULT_SENDER'] = 'rharaldmoreirag@gmail.com'

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

db.init_app(app)

with app.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Função auxiliar para carregar categorias
def load_task_categories(tasks):
    """Carrega as categorias relacionadas às tarefas."""
    for task in tasks:
        task.categories = Category.query.filter(Category.id.in_([cat.id for cat in task.categories])).all()
    return tasks

@app.route('/')
def index():
    if 'user_id' in session:
        try:
            user_id = session['user_id']
            tasks = get_tasks_with_categories(user_id)
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.completed)
            pending_tasks = total_tasks - completed_tasks
            recent_tasks = Task.query.filter_by(user_id=user_id).order_by(Task.created_at.desc()).limit(5).all()
            return render_template('index.html',
                                 total_tasks=total_tasks,
                                 completed_tasks=completed_tasks,
                                 pending_tasks=pending_tasks,
                                 recent_tasks=recent_tasks,
                                 now=datetime.datetime.now())
        except Exception as e:
            flash(f'Erro ao carregar tarefas: {e}', 'danger')
            return render_template('index.html')
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'danger')
        else:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))  # Redirect to homepage
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('index'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)  # Usar sys.stdout para console
    ]
)
logger = logging.getLogger(__name__)

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    print("\n=== Starting dashboard route ===")
    try:
        search = request.args.get('search')
        filter_priority = request.args.get('priority')
        filter_category = request.args.get('category')
        filter_status = request.args.get('status')
        filter_due_date = request.args.get('due_date')

        user_id = session.get('user_id')
        print(f"Dashboard user_id: {user_id}")
        user = User.query.get(user_id)
        
        if not user_id:
            flash('Sessão inválida. Por favor, faça login novamente.', 'danger')
            return redirect(url_for('login'))
        
        if not user:
            flash('Usuário não encontrado. Por favor, faça login novamente.', 'danger')
            return redirect(url_for('login'))
        
        print(f"Querying tasks for user {user_id}")
        tasks = Task.query.filter_by(user_id=user_id)
        print(f"Found {tasks.count()} tasks in database")
        # print(f"Task IDs: {[t.id for t in tasks.all()]}") # Isso pode ser caro se houver muitas tarefas, remova se não for necessário

        if search:
            print(f"Applying search filter: {search}")
            tasks = tasks.filter(or_(Task.title.like(f'%{search}%'), Task.description.like(f'%{search}%')))

        if filter_priority and filter_priority != 'all':
            try:
                enum_priority = Priority[filter_priority.upper()]
                print(f"Applying priority filter: {enum_priority}")
                tasks = tasks.filter(Task.priority == enum_priority)
            except KeyError:
                flash('Prioridade inválida selecionada.', 'warning')

        if filter_category and filter_category != 'all':
            print(f"Applying category filter: {filter_category}")
            tasks = tasks.join(Task.categories).filter(Category.name == filter_category)

        if filter_status and filter_status != 'all':
            print(f"Applying status filter: {filter_status}")
            if filter_status == 'pending':
                tasks = tasks.filter(Task.completed == False)
            elif filter_status == 'completed':
                tasks = tasks.filter(Task.completed == True)

        if filter_due_date:
            try:
                filter_date_obj = datetime.datetime.strptime(filter_due_date, '%Y-%m-%d').date()
                print(f"Applying due date filter: {filter_due_date}")
                tasks = tasks.filter(Task.due_date <= filter_date_obj) # Comparar com o objeto date
            except ValueError:
                flash('Formato de data inválido.', 'warning')

        tasks = tasks.all() # Execute a query aqui após todos os filtros
        print(f"Final task count after filters: {len(tasks)}")
        for task in tasks:
            print(f"Task: {task.id} - {task.title} - Priority: {task.priority} - Due: {task.due_date}")

        total_tasks = len(tasks)
        completed_tasks = sum(1 for task in tasks if task.completed)
        pending_tasks = total_tasks - completed_tasks

        priority_counts = defaultdict(int)
        for task in tasks:
            priority_value = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
            priority_counts[priority_value] += 1
        priority_labels = [p.value.capitalize() for p in Priority]
        priority_data = [priority_counts[p.value] for p in Priority]

        pending_priority_counts = defaultdict(int)
        for task in tasks:
            if not task.completed:
                priority_value = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
                pending_priority_counts[priority_value] += 1
        pending_priority_labels = [p.value.capitalize() for p in Priority]
        pending_priority_data = [pending_priority_counts[p.value] for p in Priority]

        category_counts = defaultdict(int)
        for task in tasks:
            for category in task.categories:
                # Remove aspas e espaços extras
                clean_name = category.name.strip().replace('"', '')
                category_counts[clean_name] += 1
        category_data = sorted(category_counts.items(), key=lambda item: item[0])
        
        # Debug prints
        print("\n=== Category Data Debug ===")
        print("Raw category counts:", category_counts)
        print("Category data:", category_data)
        print("All category names:", [cat.name for task in tasks for cat in task.categories])
        # A linha abaixo causou o erro. Removendo porque é apenas um print de depuração e não deveria ser código de execução normal.
        # print(f"Cleaned category names: {[clean_name for task in tasks for cat in task.categories for clean_name in [cat.name.strip().replace('\"', '')]]}")

        # Prepare tasks data with clean categories
        tasks_data = [
            {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'priority': task.priority,
                'categories': [{'name': cat.name.strip()} for cat in task.categories],  # Ensure no quotes
                'due_date': task.due_date,
                'completed': task.completed,
                'subtasks': task.subtasks
            } for task in tasks
        ]
        
        tasks_by_month = Counter()
        for t in tasks:
            if t.created_at:
                key = t.created_at.strftime('%Y-%m')
                tasks_by_month[key] += 1
        months_sorted = sorted(tasks_by_month.keys())
        tasks_per_month_labels = months_sorted
        tasks_per_month_data = [tasks_by_month[m] for m in months_sorted]

        total_subtasks = sum(len(t.subtasks) for t in tasks)
        completed_subtasks = sum([sum(1 for s in t.subtasks if s.completed) for t in tasks])
        pending_subtasks = total_subtasks - completed_subtasks

        all_categories = Category.query.all()
        now = datetime.datetime.now()
        overdue_tasks = sum(1 for task in tasks if task.due_date and task.due_date.date() < now.date() and not task.completed) # Compare apenas a data, não a hora

        print("=== Dashboard data summary ===")
        print(f"Total tasks: {total_tasks}")
        print(f"Completed tasks: {completed_tasks}")
        print(f"Pending tasks: {pending_tasks}")
        print(f"Overdue tasks: {overdue_tasks}")
        print(f"All categories: {[cat.name for cat in all_categories]}")
        
        return render_template('dashboard.html',
                               user=user,
                               total_tasks=total_tasks,
                               completed_tasks=completed_tasks,
                               pending_tasks=pending_tasks,
                               overdue_tasks=overdue_tasks,
                               tasks=tasks_data,  # Use the cleaned tasks data
                               all_categories=all_categories,
                               filter_priority=filter_priority,
                               filter_category=filter_category,
                               filter_status=filter_status,
                               filter_due_date=filter_due_date,
                               priority_labels=priority_labels,
                               priority_data=priority_data,
                               category_data=category_data,
                               now=now,
                               tasks_per_month_labels=tasks_per_month_labels,
                               tasks_per_month_data=tasks_per_month_data,
                               completed_subtasks=completed_subtasks,
                               pending_priority_labels=pending_priority_labels,
                               pending_priority_data=pending_priority_data,
                               pending_subtasks=pending_subtasks)

    except Exception as e:
        print(f"Error in dashboard: {str(e)}")
        flash(f'Erro ao carregar o dashboard: {str(e)}', 'danger') # Adicionado o erro para o flash
        return redirect(url_for('index'))
@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    user_id = session['user_id']
    all_categories = Category.query.all()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        priority_str = request.form['priority']
        due_date_str = request.form.get('due_date')
        category_names_str = request.form.get('categories')

        priority = Priority[priority_str.upper()]

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Formato de data de vencimento inválido.', 'danger')
                return redirect(url_for('add_task'))

        new_task = Task(title=title, description=description,
                        user_id=user_id, priority=priority, due_date=due_date)

        if category_names_str:
            category_names = [name.strip() for name in category_names_str.split(',') if name.strip()]
            for cat_name in category_names:
                category = Category.query.filter_by(name=cat_name).first()
                if not category:
                    category = Category(name=cat_name)
                    db.session.add(category)
                new_task.categories.append(category)

        db.session.add(new_task)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar tarefa: {e}', 'danger')
            return redirect(url_for('add_task'))

        subtask_descriptions = request.form.getlist('subtask_description[]')
        for desc in subtask_descriptions:
            if desc.strip():
                sub = SubTask(description=desc.strip(), completed=False, task=new_task)
                db.session.add(sub)
        try:
            db.session.commit()
            flash('Tarefa adicionada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar subtarefas: {e}', 'danger')

        return redirect(url_for('dashboard'))
    return render_template('add_task.html', all_categories=all_categories)

@app.route('/search_tasks', methods=['GET'])
@login_required
def search_tasks():
    search = request.args.get('search')
    filter_priority = request.args.get('priority')
    filter_category = request.args.get('category')
    filter_status = request.args.get('status')
    filter_due_date = request.args.get('due_date')

    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id)

    if search:
        tasks = tasks.filter(or_(Task.title.like(f'%{search}%'), Task.description.like(f'%{search}%')))

    if filter_priority and filter_priority != 'all':
        try:
            enum_priority = Priority[filter_priority.upper()]
            tasks = tasks.filter(Task.priority == enum_priority)
        except KeyError:
            flash('Prioridade inválida selecionada.', 'warning')

    if filter_category and filter_category != 'all':
        tasks = tasks.join(Task.categories).filter(Category.name == filter_category)

    if filter_status and filter_status != 'all':
        if filter_status == 'pending':
            tasks = tasks.filter(Task.completed == False)
        elif filter_status == 'completed':
            tasks = tasks.filter(Task.completed == True)

    if filter_due_date:
        try:
            filter_date_obj = datetime.datetime.strptime(filter_due_date, '%Y-%m-%d').date()
            tasks = tasks.filter(Task.due_date <= filter_due_date)
        except ValueError:
            flash('Formato de data inválido.', 'warning')

    tasks = tasks.all()
    now = datetime.datetime.now()

    return render_template('tasks.html', tasks=tasks, now=now)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        flash('Você não tem permissão para editar esta tarefa.', 'danger')
        return redirect(url_for('dashboard'))

    all_categories = Category.query.all()

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form.get('description')
        task.priority = Priority[request.form['priority'].upper()]
        due_date_str = request.form.get('due_date')
        if due_date_str:
            try:
                task.due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Formato de data de vencimento inválido.', 'danger')
                return redirect(url_for('edit_task', task_id=task.id))
        else:
            task.due_date = None

        task.completed = 'completed' in request.form

        category_names_str = request.form.get('categories')
        task.categories.clear()
        if category_names_str:
            category_names = [name.strip() for name in category_names_str.split(',') if name.strip()]
            for cat_name in category_names:
                category = Category.query.filter_by(name=cat_name).first()
                if not category:
                    category = Category(name=cat_name)
                    db.session.add(category)
                task.categories.append(category)

        SubTask.query.filter_by(task_id=task.id).delete()
        subtask_descriptions = request.form.getlist('subtask_description[]')
        subtask_completeds = request.form.getlist('subtask_completed[]')
        for idx, desc in enumerate(subtask_descriptions):
            if desc.strip():
                completed = str(idx) in subtask_completeds
                sub = SubTask(description=desc.strip(), completed=completed, task=task)
                db.session.add(sub)
        try:
            db.session.commit()
            flash('Tarefa atualizada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar tarefa: {e}', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('edit_task.html', task=task, all_categories=all_categories)

@app.route('/toggle_subtask/<int:subtask_id>', methods=['POST'])
@login_required
def toggle_subtask(subtask_id):
    sub = SubTask.query.get_or_404(subtask_id)
    task = Task.query.get(sub.task_id)
    if task.user_id != session['user_id']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Você não tem permissão para modificar esta subtarefa.'}), 403
        flash('Você não tem permissão para modificar esta subtarefa.', 'danger')
        return redirect(url_for('dashboard'))
    sub.completed = not sub.completed
    try:
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': 'Checklist atualizado!'}), 200
        flash('Checklist atualizado!', 'success')
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': f'Erro ao atualizar subtarefa: {e}'}), 500
        flash(f'Erro ao atualizar subtarefa: {e}', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Você não tem permissão para excluir esta tarefa.'}), 403
        flash('Você não tem permissão para excluir esta tarefa.', 'danger')
        return redirect(url_for('dashboard'))
    try:
        db.session.delete(task)
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': 'Tarefa excluída com sucesso!'}), 200
        flash('Tarefa excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': f'Erro ao excluir tarefa: {e}'}), 500
        flash(f'Erro ao excluir tarefa: {e}', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Você não tem permissão para modificar esta tarefa.'}), 403
        flash('Você não tem permissão para modificar esta tarefa.', 'danger')
        return redirect(url_for('dashboard'))
    task.completed = not task.completed
    try:
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': 'Status da tarefa atualizado!'}), 200
        flash('Status da tarefa atualizado!', 'success')
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': f'Erro ao atualizar status: {e}'}), 500
        flash(f'Erro ao atualizar status: {e}', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        user_id = session['user_id']
        user = User.query.get(user_id)
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if not check_password_hash(user.password, current_password):
            flash('Senha atual incorreta.', 'danger')
            return redirect(url_for('change_password'))
        if new_password != confirm_password:
            flash('A nova senha e a confirmação não coincidem.', 'danger')
            return redirect(url_for('change_password'))
        if len(new_password) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('change_password'))
        user.password = generate_password_hash(new_password)
        try:
            db.session.commit()
            flash('Sua senha foi alterada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao alterar senha: {e}', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('change_password.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.id, salt='password-reset')
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message('Redefinição de Senha - Task Manager',
                          recipients=[user.email])
            msg.body = f'''
Para redefinir sua senha, clique no seguinte link:
{reset_link}

Se você não solicitou isso, ignore este e-mail.
'''
            try:
                mail.send(msg)
                flash('Um link de redefinição de senha foi enviado para seu e-mail.', 'info')
            except Exception as e:
                flash(f'Erro ao enviar e-mail: {e}. Verifique as configurações do servidor de e-mail.', 'danger')
        else:
            flash('Nenhuma conta encontrada com este e-mail.', 'danger')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        user_id = serializer.loads(token, salt='password-reset', max_age=3600)
        user = User.query.get(user_id)
        if not user:
            flash('Link de redefinição inválido.', 'danger')
            return redirect(url_for('forgot_password'))
    except SignatureExpired:
        flash('O link de redefinição expirou. Solicite um novo.', 'danger')
        return redirect(url_for('forgot_password'))
    except Exception as e:
        flash('Link de redefinição inválido.', 'danger')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('A nova senha e a confirmação não coincidem.', 'danger')
            return redirect(url_for('reset_password', token=token))
        if len(new_password) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('reset_password', token=token))
        user.password = generate_password_hash(new_password)
        try:
            db.session.commit()
            flash('Sua senha foi redefinida com sucesso! Faça login.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao redefinir senha: {e}', 'danger')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

@app.route('/export/pdf')
@login_required
def export_pdf():
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id).all()
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Relatório de Tarefas")
    pdf.setFont("Helvetica", 12)
    y -= 30

    for task in tasks:
        pdf.drawString(40, y, f"Título: {task.title}")
        y -= 18
        pdf.drawString(60, y, f"Descrição: {task.description or ''}")
        y -= 18
        prioridade = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
        pdf.drawString(60, y, f"Prioridade: {prioridade.capitalize()}")
        y -= 18
        categorias = ', '.join([c.name for c in task.categories]) if task.categories else 'N/A'
        pdf.drawString(60, y, f"Categorias: {categorias}")
        y -= 18
        vencimento = task.due_date.strftime('%d/%m/%Y') if task.due_date else 'N/A'
        pdf.drawString(60, y, f"Vencimento: {vencimento}")
        y -= 18
        status = 'Concluída' if task.completed else 'Pendente'
        pdf.drawString(60, y, f"Status: {status}")
        y -= 18
        if task.subtasks:
            pdf.drawString(60, y, "Subtarefas:")
            y -= 18
            for sub in task.subtasks:
                checked = "" if sub.completed else ""
                pdf.drawString(80, y, f"[{checked}] {sub.description}")
                y -= 16
                if y < 60:
                    pdf.showPage()
                    y = height - 40
        y -= 12
        if y < 60:
            pdf.showPage()
            y = height - 40

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="tarefas.pdf", mimetype='application/pdf')

@app.route('/export/excel')
@login_required
def export_excel():
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id).all()
    data = []
    for task in tasks:
        prioridade = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
        categorias = ", ".join([c.name for c in task.categories]) if task.categories else ""
        vencimento = task.due_date.strftime('%d/%m/%Y') if task.due_date else ""
        status = "Concluída" if task.completed else "Pendente"
        subtarefas = "\n".join([f"[{'x' if s.completed else ' '}] {s.description}" for s in task.subtasks])
        data.append({
            "Título": task.title,
            "Descrição": task.description or "",
            "Prioridade": prioridade.capitalize(),
            "Categorias": categorias,
            "Vencimento": vencimento,
            "Status": status,
            "Subtarefas": subtarefas
        })
    df = pd.DataFrame(data)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Tarefas")
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="tarefas.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(debug=True)