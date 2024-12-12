from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import User, db, UserRole
from forms import AgentForm
from decorators import admin_required
from sqlalchemy.exc import IntegrityError

bp = Blueprint('agents', __name__, url_prefix='/agents')

@bp.route('/')
@login_required
@admin_required
def list_agents():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = User.query.filter_by(role=UserRole.AGENTE).order_by(User.username)
    
    # Aplicar filtros de búsqueda si existen
    username = request.args.get('username', '')
    email = request.args.get('email', '')
    
    if username:
        query = query.filter(User.username.ilike(f'%{username}%'))
    if email:
        query = query.filter(User.email.ilike(f'%{email}%'))
    
    # Obtener la paginación
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    total = query.count()
    agents = pagination.items
    
    return render_template('agents/list.html',
                         agents=agents,
                         pagination=pagination,
                         total=total,
                         page=page,
                         per_page=per_page)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_agent():
    form = AgentForm()
    form.parent_id.choices = [(0, 'Ninguno')] + [(a.id, a.username) for a in User.query.filter_by(role=UserRole.AGENTE).all()]
    if form.validate_on_submit():
        try:
            agent = User(
                username=form.username.data,
                email=form.email.data,
                role=UserRole.AGENTE,
                name=form.name.data,
                phone=form.phone.data,
                address=form.address.data,
                date_of_birth=form.date_of_birth.data,
                hire_date=form.hire_date.data,
                document_type=form.document_type.data,
                document_number=form.document_number.data,
                parent_id=form.parent_id.data if form.parent_id.data != 0 else None
            )
            agent.set_password(form.password.data)
            db.session.add(agent)
            db.session.commit()
            flash('Agente creado exitosamente.')
            return redirect(url_for('agents.list_agents'))
        except IntegrityError as e:
            db.session.rollback()
            if 'uq_user_document' in str(e):
                flash('Ya existe un agente con ese número de documento.', 'error')
            elif 'username' in str(e):
                flash('El nombre de usuario ya está en uso.', 'error')
            elif 'email' in str(e):
                flash('El correo electrónico ya está en uso.', 'error')
            else:
                flash('Error al crear el agente: Datos duplicados.', 'error')
    return render_template('agents/create.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_agent(id):
    agent = User.query.get_or_404(id)
    form = AgentForm(obj=agent)
    form.id.data = str(id)
    
    # Configurar las opciones del supervisor excluyendo al agente actual
    supervisors = [(0, 'Ninguno')] + [
        (a.id, a.username) 
        for a in User.query.filter_by(role=UserRole.AGENTE).all() 
        if a.id != id
    ]
    form.parent_id.choices = supervisors
    
    if form.validate_on_submit():
        try:
            # Actualizar campos básicos
            form.populate_obj(agent)
            
            # Manejar el campo de contraseña separadamente
            if form.password.data:
                agent.set_password(form.password.data)
                
            # Manejar el supervisor
            agent.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
            
            db.session.commit()
            flash('Agente actualizado exitosamente.')
            return redirect(url_for('agents.list_agents'))
            
        except IntegrityError as e:
            db.session.rollback()
            if 'uq_user_document' in str(e):
                flash('Ya existe un agente con ese número de documento.', 'error')
            elif 'username' in str(e):
                flash('El nombre de usuario ya está en uso.', 'error')
            elif 'email' in str(e):
                flash('El correo electrónico ya está en uso.', 'error')
            else:
                flash('Error al actualizar el agente: Datos duplicados.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el agente: {str(e)}', 'error')
            
    # Si hay errores en el formulario, mostrarlos
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error en {getattr(form, field).label.text}: {error}', 'error')
            
    return render_template('agents/edit.html', form=form, agent=agent)

@bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_agent(id):
    agent = User.query.get_or_404(id)
    db.session.delete(agent)
    db.session.commit()
    flash('Agente eliminado exitosamente.')
    return redirect(url_for('agents.list_agents'))
