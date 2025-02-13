from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import User, db, UserRole
from forms import AgentForm
from decorators import admin_required
from utils.url_helpers import get_return_url
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
    if form.validate_on_submit():
        try:
            form.populate_obj(agent)
            db.session.commit()
            flash('Agente actualizado exitosamente', 'success')
            return redirect(get_return_url(url_for('agents.list_agents')))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un usuario con ese nombre de usuario o email', 'error')
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
