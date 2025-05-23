from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from models import db, User, Task, Category, Priority # Certifique-se que Priority é importado
from werkzeug.security import generate_password_hash, check_password_hash
import os
from collections import defaultdict
import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message
from functools import wraps # Importar wraps aqui

# Novos imports para exportação
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Use uma chave mais segura em produção
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração do Flask-Mail (Substitua pelos seus dados reais)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rharaldmoreirag@gmail.com'  # Substitua pelo seu e-mail
app.config['MAIL_PASSWORD'] = 'czrc uxli kxet vtwc'  # Substitua pela senha de aplicativo (gerada no Google Account Security -> App passwords)
app.config['MAIL_DEFAULT_SENDER'] = 'rharaldmoreirag@gmail.com'

# Inicializar Flask-Mail e Serializer
mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Inicializar o SQLAlchemy com o app
db.init_app(app)

# Criar as tabelas dentro do contexto da aplicação
with app.app_context():
    db.create_all()

# Decorator para exigir login
def login_required(f):
    @wraps(f) # Adiciona @wraps para preservar metadados da função original
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ------------- EXPORTAÇÃO PDF/EXCEL ----------------
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
        y -= 30
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
        data.append({
            "Título": task.title,
            "Descrição": task.description or "",
            "Prioridade": prioridade.capitalize(),
            "Categorias": categorias,
            "Vencimento": vencimento,
            "Status": status
        })
    df = pd.DataFrame(data)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Tarefas")
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="tarefas.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ---------------- ROTAS PADRÃO --------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
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
            return redirect(url_for('dashboard'))
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

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    user_id = session['user_id']
    user = User.query.get(user_id)

    # Obter todas as tarefas do usuário
    user_tasks = Task.query.filter_by(user_id=user_id).all()

    # Estatísticas de tarefas
    total_tasks = len(user_tasks)
    completed_tasks = sum(1 for task in user_tasks if task.completed)
    pending_tasks = total_tasks - completed_tasks

    # Dados para gráfico de prioridade
    priority_counts = defaultdict(int)
    for task in user_tasks:
        # Corrige se Priority for Enum, senão pega string
        priority_value = task.priority.value if hasattr(task.priority, 'value') else str(task.priority)
        priority_counts[priority_value] += 1
    
    # Garante que todas as prioridades sejam incluídas, mesmo que com 0 tarefas
    priority_labels = [p.value.capitalize() for p in Priority]
    priority_data = [priority_counts[p.value] for p in Priority]

    # Dados para tarefas por categoria
    category_counts = defaultdict(int)
    for task in user_tasks:
        for category in task.categories:
            category_counts[category.name] += 1
    
    # Preparar dados para o template, ordenando por nome da categoria
    category_data = sorted(category_counts.items(), key=lambda item: item[0])

    # Filtragem de tarefas
    filter_priority = request.args.get('priority')
    filter_category = request.args.get('category')
    filter_status = request.args.get('status')
    filter_due_date = request.args.get('due_date')

    filtered_tasks = user_tasks

    if filter_priority and filter_priority != 'all':
        try:
            enum_priority = Priority[filter_priority.upper()]
            filtered_tasks = [task for task in filtered_tasks if task.priority == enum_priority]
        except KeyError:
            flash('Prioridade inválida selecionada.', 'warning')

    if filter_category and filter_category != 'all':
        filtered_tasks = [task for task in filtered_tasks if any(cat.name == filter_category for cat in task.categories)]

    if filter_status and filter_status != 'all':
        if filter_status == 'completed':
            filtered_tasks = [task for task in filtered_tasks if task.completed]
        elif filter_status == 'pending':
            filtered_tasks = [task for task in filtered_tasks if not task.completed]

    if filter_due_date:
        try:
            filter_date_obj = datetime.datetime.strptime(filter_due_date, '%Y-%m-%d').date()
            filtered_tasks = [task for task in filtered_tasks if task.due_date and task.due_date.date() <= filter_date_obj and not task.completed]
        except ValueError:
            flash('Formato de data inválido.', 'warning')

    filtered_tasks.sort(key=lambda x: (x.completed, x.due_date if x.due_date else datetime.datetime.max, x.priority.value if hasattr(x.priority, 'value') else str(x.priority)))

    all_categories = Category.query.all()
    now = datetime.datetime.now()

    return render_template('dashboard.html',
                           user=user,
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks,
                           pending_tasks=pending_tasks,
                           tasks=filtered_tasks,
                           all_categories=all_categories,
                           filter_priority=filter_priority,
                           filter_category=filter_category,
                           filter_status=filter_status,
                           filter_due_date=filter_due_date,
                           priority_labels=priority_labels,
                           priority_data=priority_data,
                           category_data=category_data,
                           now=now
                           )

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

        print(f"DEBUG: String de categorias recebida: '{category_names_str}'") # DEBUG PRINT

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
        
        # Adicionar categorias
        if category_names_str:
            category_names = [name.strip() for name in category_names_str.split(',') if name.strip()]
            print(f"DEBUG: Nomes de categorias processados: {category_names}") # DEBUG PRINT
            for cat_name in category_names:
                category = Category.query.filter_by(name=cat_name).first()
                if not category:
                    print(f"DEBUG: Criando nova categoria: {cat_name}") # DEBUG PRINT
                    category = Category(name=cat_name)
                    db.session.add(category)
                new_task.categories.append(category)

        db.session.add(new_task)
        try:
            db.session.commit()
            flash('Tarefa adicionada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback() # Reverte a transação em caso de erro
            flash(f'Erro ao adicionar tarefa: {e}', 'danger')
            print(f"ERRO: Falha ao adicionar tarefa ou categoria: {e}") # DEBUG PRINT
        
        return redirect(url_for('dashboard'))
    return render_template('add_task.html', all_categories=all_categories)


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

        # Atualizar categorias
        category_names_str = request.form.get('categories')
        task.categories.clear() # Limpa as categorias existentes
        if category_names_str:
            category_names = [name.strip() for name in category_names_str.split(',') if name.strip()]
            for cat_name in category_names:
                category = Category.query.filter_by(name=cat_name).first()
                if not category:
                    category = Category(name=cat_name)
                    db.session.add(category)
                task.categories.append(category)
        
        try:
            db.session.commit()
            flash('Tarefa atualizada com sucesso!', 'success')
        except Exception as e:
            db.session.rollback() # Reverte a transação em caso de erro
            flash(f'Erro ao atualizar tarefa: {e}', 'danger')
            print(f"ERRO: Falha ao atualizar tarefa ou categoria: {e}") # DEBUG PRINT
            
        return redirect(url_for('dashboard'))
    
    return render_template('edit_task.html', task=task, all_categories=all_categories)

@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        flash('Você não tem permissão para excluir esta tarefa.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        db.session.delete(task)
        db.session.commit()
        flash('Tarefa excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir tarefa: {e}', 'danger')
        print(f"ERRO: Falha ao excluir tarefa: {e}")
        
    return redirect(url_for('dashboard'))

@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.user_id != session['user_id']:
        flash('Você não tem permissão para modificar esta tarefa.', 'danger')
        return redirect(url_for('dashboard'))
    
    task.completed = not task.completed # Alterna o status
    try:
        db.session.commit()
        flash('Status da tarefa atualizado!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status: {e}', 'danger')
        print(f"ERRO: Falha ao atualizar status da tarefa: {e}")

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
            print(f"ERRO: Falha ao alterar senha: {e}")
        
        return redirect(url_for('dashboard'))
    return render_template('change_password.html')

# Esqueci a senha
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
                print(f"Erro ao enviar e-mail: {e}") # Para depuração no console
        else:
            flash('Nenhuma conta encontrada com este e-mail.', 'danger')
            
        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

# Redefinir senha
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        user_id = serializer.loads(token, salt='password-reset', max_age=3600)  # Token válido por 1 hora
        user = User.query.get(user_id)
        if not user: # Verifica se o usuário existe para o ID do token
            flash('Link de redefinição inválido.', 'danger')
            return redirect(url_for('forgot_password'))
    except SignatureExpired:
        flash('O link de redefinição expirou. Solicite um novo.', 'danger')
        return redirect(url_for('forgot_password'))
    except Exception as e: # Captura exceções mais gerais para link inválido
        flash('Link de redefinição inválido.', 'danger')
        print(f"Erro ao carregar token: {e}") # Para depuração
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
            print(f"ERRO: Falha ao redefinir senha: {e}")
            
        return redirect(url_for('login')) # Redireciona para login após redefinição
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    app.run(debug=True)