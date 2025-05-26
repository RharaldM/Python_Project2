from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime as dt
from functools import wraps
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from collections import defaultdict, Counter
from models import db, User, Task, Category, Priority, SubTask
import os
import pandas as pd
from io import BytesIO
from flask import send_file

routes = Blueprint('routes', __name__, url_prefix='/')

# Função auxiliar para registrar todas as rotas
# Removida a função register_routes pois não é necessária

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'danger')
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'danger')
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_tasks_with_categories(user_id):
    return Task.query.options(joinedload(Task.categories)).filter_by(user_id=user_id).all()

@routes.route('/')
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
                                 now=dt.now())
        except Exception as e:
            flash(f'Erro ao carregar tarefas: {e}', 'danger')
            return render_template('index.html')
    return render_template('index.html')

@routes.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('routes.login'))
    return render_template('register.html')

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('routes.dashboard'))
        else:
            flash('Nome de usuário ou senha inválidos.', 'danger')
    return render_template('login.html')

@routes.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('routes.index'))

@routes.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    search = request.args.get('search')
    filter_priority = request.args.get('priority')
    filter_category = request.args.get('category')
    filter_status = request.args.get('status')
    filter_due_date = request.args.get('due_date')

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user_id:
        flash('Sessão inválida. Por favor, faça login novamente.', 'danger')
        return redirect(url_for('routes.login'))
    
    if not user:
        flash('Usuário não encontrado. Por favor, faça login novamente.', 'danger')
        return redirect(url_for('routes.login'))

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
            filter_date_obj = dt.strptime(filter_due_date, '%Y-%m-%d').date()
            tasks = tasks.filter(Task.due_date <= filter_date_obj)
        except ValueError:
            flash('Formato de data inválido.', 'warning')

    tasks = tasks.all()
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
            clean_name = category.name.strip().replace('"', '')
            category_counts[clean_name] += 1
    category_data = sorted(category_counts.items(), key=lambda item: item[0])

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
    now = dt.now()
    overdue_tasks = sum(1 for task in tasks if task.due_date and task.due_date.date() < now.date() and not task.completed)

    tasks_data = [
        {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'categories': [{'name': cat.name.strip()} for cat in task.categories],
            'due_date': task.due_date,
            'completed': task.completed,
            'subtasks': task.subtasks
        } for task in tasks
    ]

    return render_template('dashboard.html',
                           user=user,
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks,
                           pending_tasks=pending_tasks,
                           overdue_tasks=overdue_tasks,
                           tasks=tasks_data,
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

@routes.route('/add_task', methods=['GET', 'POST'])
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

        try:
            priority = Priority[priority_str.upper()]
        except KeyError:
            # Se a prioridade não for válida, usamos a prioridade padrão 'MEDIA'
            priority = Priority.MEDIA
            flash('Prioridade inválida. Usando prioridade média.', 'warning')

        due_date = None
        if due_date_str:
            try:
                due_date = dt.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Formato de data de vencimento inválido.', 'danger')
                return redirect(url_for('routes.add_task'))

        new_task = Task(title=title, description=description,
                        user_id=user_id, priority=priority, due_date=due_date)

        if category_names_str:
            category_names = [name.strip() for name in category_names_str.split(',') if name.strip()]
            for cat_name in category_names:
                category = Category.query.filter_by(name=cat_name).first()
                if not category:
                    category = Category(name=cat_name)
                    db.session.add(category)
                
                # Adicionar a categoria e fazer commit
                new_task.categories.append(category)
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    # Se houver erro de unicidade, remover a categoria e continuar
                    if 'UNIQUE constraint failed' in str(e):
                        new_task.categories.remove(category)
                        flash(f'Categoria "{cat_name}" já está associada à tarefa.', 'warning')
                    else:
                        raise e

        db.session.add(new_task)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar tarefa: {e}', 'danger')
            return redirect(url_for('routes.add_task'))

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

        return redirect(url_for('routes.dashboard'))
    return render_template('add_task.html', all_categories=all_categories)

@routes.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        flash('Você não tem permissão para editar esta tarefa.', 'danger')
        return redirect(url_for('routes.dashboard'))

    all_categories = Category.query.all()

    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form.get('description')
        try:
            task.priority = Priority[request.form['priority'].upper()]
        except KeyError:
            # Se a prioridade não for válida, usamos a prioridade padrão 'MEDIA'
            task.priority = Priority.MEDIA
            flash('Prioridade inválida. Usando prioridade média.', 'warning')
        due_date_str = request.form.get('due_date')
        if due_date_str:
            try:
                task.due_date = dt.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Formato de data de vencimento inválido.', 'danger')
                return redirect(url_for('routes.edit_task', task_id=task.id))
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
        return redirect(url_for('routes.dashboard'))

    return render_template('edit_task.html', task=task, all_categories=all_categories)

@routes.route('/toggle_subtask/<int:subtask_id>', methods=['POST'])
@login_required
def toggle_subtask(subtask_id):
    sub = SubTask.query.get_or_404(subtask_id)
    task = Task.query.get(sub.task_id)
    if task.user_id != session['user_id']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Você não tem permissão para modificar esta subtarefa.'}), 403
        flash('Você não tem permissão para modificar esta subtarefa.', 'danger')
        return redirect(url_for('routes.dashboard'))
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
    return redirect(url_for('routes.dashboard'))

@routes.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Você não tem permissão para excluir esta tarefa.'}), 403
        flash('Você não tem permissão para excluir esta tarefa.', 'danger')
        return redirect(url_for('routes.dashboard'))
    try:
        # Primeiro excluímos todas as subtarefas
        SubTask.query.filter_by(task_id=task_id).delete()
        
        # Depois excluímos a tarefa principal
        db.session.delete(task)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': 'Tarefa excluída com sucesso!'}), 200
        flash('Tarefa excluída com sucesso!', 'success')
        return redirect(url_for('routes.dashboard'))
    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': f'Erro ao excluir tarefa: {e}'}), 500
        flash(f'Erro ao excluir tarefa: {e}', 'danger')
        return redirect(url_for('routes.dashboard'))

@routes.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Você não tem permissão para modificar esta tarefa.'}), 403
        flash('Você não tem permissão para modificar esta tarefa.', 'danger')
        return redirect(url_for('routes.dashboard'))
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
    return redirect(url_for('routes.dashboard'))

@routes.route('/change_password', methods=['GET', 'POST'])
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
            return redirect(url_for('routes.change_password'))
        if new_password != confirm_password:
            flash('A nova senha e a confirmação não coincidem.', 'danger')
            return redirect(url_for('routes.change_password'))
        if len(new_password) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('routes.change_password'))
        user.password = generate_password_hash(new_password)
        try:
            db.session.commit()
            flash('Sua senha foi alterada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao alterar senha: {e}', 'danger')
        return redirect(url_for('routes.dashboard'))
    return render_template('change_password.html')

@routes.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.id, salt='password-reset')
            reset_link = url_for('routes.reset_password', token=token, _external=True)
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
        return redirect(url_for('routes.forgot_password'))
    return render_template('forgot_password.html')

@routes.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        user_id = serializer.loads(token, salt='password-reset', max_age=3600)
        user = User.query.get(user_id)
        if not user:
            flash('Link de redefinição inválido.', 'danger')
            return redirect(url_for('routes.forgot_password'))
    except SignatureExpired:
        flash('O link de redefinição expirou. Solicite um novo.', 'danger')
        return redirect(url_for('routes.forgot_password'))
    except Exception as e:
        flash('Link de redefinição inválido.', 'danger')
        return redirect(url_for('routes.forgot_password'))
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('A nova senha e a confirmação não coincidem.', 'danger')
            return redirect(url_for('routes.reset_password', token=token))
        if len(new_password) < 6:
            flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('routes.reset_password', token=token))
        user.password = generate_password_hash(new_password)
        try:
            db.session.commit()
            flash('Sua senha foi redefinida com sucesso! Faça login.', 'success')
        except Exception as e:
            flash(f'Erro ao redefinir senha: {e}', 'danger')
        return redirect(url_for('routes.login'))
    return render_template('reset_password.html', token=token)

@routes.route('/export_excel')
@login_required
def export_excel():
    user_id = session['user_id']
    tasks = get_tasks_with_categories(user_id)
    
    # Criar DataFrame com as informações das tarefas
    data = []
    for task in tasks:
        data.append({
            'Título': task.title,
            'Descrição': task.description,
            'Data de Criação': task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Data de Vencimento': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            'Status': 'Concluída' if task.completed else 'Pendente',
            'Prioridade': task.priority.name if task.priority else '',
            'Categorias': ', '.join([cat.name for cat in task.categories]) if task.categories else '',
            'Subtarefas': ', '.join([f"[{sub.completed and 'x' or ' '}] {sub.description}" for sub in task.subtasks]) if task.subtasks else ''
        })
    
    df = pd.DataFrame(data)
    
    # Criar Excel em memória
    excel_file = BytesIO()
    writer = pd.ExcelWriter(excel_file, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Tarefas')
    writer.close()
    
    # Configurar o cursor para o início do arquivo
    excel_file.seek(0)
    
    # Enviar o arquivo para download
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='tarefas.xlsx'
    )

@routes.route('/export_pdf')
@login_required
def export_pdf():
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id).all()
    
    # Criar DataFrame com as informações das tarefas
    data = []
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
                checked = "x" if sub.completed else " "
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
