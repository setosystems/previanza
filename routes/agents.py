from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required
from models import User, db, UserRole, DocumentType
from forms import AgentForm
from decorators import admin_required
from utils.url_helpers import get_return_url
from sqlalchemy.exc import IntegrityError

bp = Blueprint('agents', __name__, url_prefix='/agents')

@bp.route('/')
@login_required
@admin_required
def list_agents():
    # Hacer la sesión permanente al entrar a esta vista
    session.permanent = True
    
    # Guardar/recuperar parámetros de paginación, filtros y ordenamiento en la sesión
    session_key = 'agents_list_params'
    
    # Si hay parámetros en la solicitud, actualizar la sesión
    if request.args:
        # Limpiar la sesión si se hace una nueva búsqueda (cuando hay parámetros pero no hay page)
        if 'name' in request.args and 'page' not in request.args:
            if session_key in session:
                session.pop(session_key)
                
        # Guardar los parámetros actuales en la sesión
        session[session_key] = {
            'name': request.args.get('name', ''),
            'email': request.args.get('email', ''),
            'document': request.args.get('document', ''),
            'sort_by': request.args.get('sort_by', 'name'),
            'sort_order': request.args.get('sort_order', 'asc'),
            'page': request.args.get('page', 1, type=int),
            'per_page': request.args.get('per_page', 10, type=int)
        }
    
    # Si no hay parámetros pero sí hay sesión guardada, recuperarla para mantener el estado
    elif session_key in session:
        return redirect(url_for('agents.list_agents', **session[session_key]))
    
    # Obtener los parámetros ya sea de la solicitud o de la sesión
    params = session.get(session_key, {})
    name = params.get('name', request.args.get('name', ''))
    email = params.get('email', request.args.get('email', ''))
    document = params.get('document', request.args.get('document', ''))
    
    # Parámetros de ordenamiento
    sort_by = params.get('sort_by', request.args.get('sort_by', 'name'))
    sort_order = params.get('sort_order', request.args.get('sort_order', 'asc'))
    
    # Mapeo de nombres de parámetros a atributos de modelo para ordenamiento
    sort_columns = {
        'name': User.name,
        'email': User.email,
        'document_number': User.document_number
    }
    
    query = User.query.filter_by(role=UserRole.AGENTE)
    if name:
        query = query.filter(User.name.ilike(f'%{name}%'))
    if email:
        query = query.filter(User.email.ilike(f'%{email}%'))
    if document:
        query = query.filter(User.document_number.ilike(f'%{document}%'))
    
    # Aplicar ordenamiento
    if sort_by in sort_columns:
        if sort_order == 'desc':
            query = query.order_by(sort_columns[sort_by].desc())
        else:
            query = query.order_by(sort_columns[sort_by].asc())
    else:
        # Ordenamiento por defecto
        query = query.order_by(User.name)
    
    page = params.get('page', request.args.get('page', 1, type=int))
    per_page = params.get('per_page', request.args.get('per_page', 10, type=int))
    
    allowed_per_page = [10, 25, 50, 100]
    if per_page not in allowed_per_page:
        per_page = 10
    
    pagination = query.paginate(
        page=page, 
        per_page=per_page,
        error_out=False
    )
    
    return render_template('agents/list.html', 
                         agents=pagination.items, 
                         document_types=DocumentType, 
                         pagination=pagination,
                         title="Lista de Agentes",
                         sort_by=sort_by,
                         sort_order=sort_order)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_agent():
    form = AgentForm()
    if form.validate_on_submit():
        try:
            agent = User(
                username=form.username.data,
                email=form.email.data,
                role=UserRole.AGENTE,
                document_type=form.document_type.data,
                document_number=form.document_number.data,
                name=form.name.data,
                phone=form.phone.data,
                address=form.address.data,
                date_of_birth=form.date_of_birth.data,
                hire_date=form.hire_date.data,
                parent_id=form.parent_id.data if form.parent_id.data != 0 else None
            )
            if form.password.data:
                agent.set_password(form.password.data)
            db.session.add(agent)
            db.session.commit()
            flash('Agente creado exitosamente', 'success')
            return redirect(get_return_url(url_for('agents.list_agents')))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un usuario con ese nombre de usuario o email', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el agente: {str(e)}', 'error')
    
    return render_template('agents/create.html', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_agent(id):
    agent = User.query.get_or_404(id)
    if agent.role != UserRole.AGENTE:
        flash('El usuario no es un agente', 'error')
        return redirect(url_for('agents.list_agents'))
    
    form = AgentForm(obj=agent)
    # Establecer el ID del agente para la validación
    form.id.data = str(agent.id)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(agent)
            db.session.commit()
            flash('Agente actualizado exitosamente', 'success')
            return redirect(get_return_url(url_for('agents.list_agents')))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el agente: {str(e)}', 'error')
    
    return render_template('agents/edit.html', form=form, agent=agent)

@bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_agent(id):
    agent = User.query.get_or_404(id)
    if agent.role != UserRole.AGENTE:
        flash('El usuario no es un agente', 'error')
        return redirect(url_for('agents.list_agents'))
    
    try:
        db.session.delete(agent)
        db.session.commit()
        flash('Agente eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el agente: {str(e)}', 'error')
    
    return redirect(get_return_url(url_for('agents.list_agents')))
