from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, abort
from flask_login import login_required, current_user
from models import Policy, Client, Product, User, db, UserRole, EmisionStatus, PaymentStatus, Commission
from forms import PolicyForm
from decorators import admin_or_digitador_required, admin_required, admin_or_digitador_or_agent_required
from werkzeug.utils import secure_filename
import openpyxl
import os
import logging
from decimal import Decimal, InvalidOperation
from dateutil import parser  # Importar el módulo para analizar fechas
from sqlalchemy.exc import OperationalError  # Añadir esta línea para importar OperationalError
import sqlalchemy
import sqlalchemy.exc  # Agregar esta línea
from utils.url_helpers import get_return_url
from datetime import datetime, date

bp = Blueprint('policies', __name__, url_prefix='/policies')

@bp.route('/')
@login_required
@admin_or_digitador_or_agent_required
def list_policies():
    policy_number = request.args.get('policy_number', '')
    client_name = request.args.get('client_name', '')
    product_name = request.args.get('product_name', '')
    
    query = Policy.query
    if policy_number:
        query = query.filter(Policy.policy_number.ilike(f'%{policy_number}%'))
    if client_name:
        query = query.join(Client).filter(Client.name.ilike(f'%{client_name}%'))
    if product_name:
        query = query.join(Product).filter(Product.name.ilike(f'%{product_name}%'))
    
    if current_user.role == UserRole.AGENTE:
        query = query.filter_by(agent_id=current_user.id)
    
    # Ordenar por número de póliza
    query = query.order_by(Policy.policy_number)
    
    # Configuración de paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    allowed_per_page = [10, 25, 50, 100]
    if per_page not in allowed_per_page:
        per_page = 10
    
    pagination = query.paginate(
        page=page, 
        per_page=per_page,
        error_out=False
    )
    
    return render_template('policies/list.html', 
                         policies=pagination.items,
                         pagination=pagination,
                         title="Lista de Pólizas")

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def create_policy():
    form = PolicyForm()
    # Cargar las opciones de productos
    products = Product.query.all()
    form.product_id.choices = [(p.id, p.name) for p in products]
    
    if form.validate_on_submit():
        try:
            # Crear la póliza sin usar populate_obj
            policy = Policy(
                policy_number=form.policy_number.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                premium=form.premium.data,
                product_id=form.product_id.data,
                client_id=form.client_id.data,
                agent_id=form.agent_id.data,
                emision_status=form.emision_status.data,
                payment_status=form.payment_status.data
            )
            
            if current_user.role == UserRole.AGENTE:
                policy.agent_id = current_user.id
            
            db.session.add(policy)
            db.session.commit()
            flash('Póliza creada exitosamente', 'success')
            return redirect(get_return_url(url_for('policies.list_policies')))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la póliza: {str(e)}', 'error')
    
    return render_template('policies/create.html', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def edit_policy(id):
    policy = Policy.query.get_or_404(id)
    form = PolicyForm(obj=policy)
    # Establecer el ID de la póliza para la validación
    form.id.data = str(policy.id)
    
    # Cargar las opciones de productos
    products = Product.query.all()
    form.product_id.choices = [(p.id, p.name) for p in products]
    
    # Cargar el cliente y agente actuales si el formulario no ha sido enviado
    if not form.is_submitted():
        if policy.client:
            form.client.data = policy.client.name
            form.client_id.data = policy.client_id
        if policy.agent:
            form.agent.data = policy.agent.name
            form.agent_id.data = policy.agent_id
    
    if form.validate_on_submit():
        try:
            form.populate_obj(policy)
            db.session.commit()
            flash('Póliza actualizada exitosamente', 'success')
            return redirect(get_return_url(url_for('policies.list_policies')))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la póliza: {str(e)}', 'error')
    
    return render_template('policies/edit.html', form=form, policy=policy)

@bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_policy(id):
    policy = Policy.query.get_or_404(id)
    try:
        db.session.delete(policy)
        db.session.commit()
        flash('Póliza eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar la póliza: {str(e)}', 'error')
    
    return redirect(get_return_url(url_for('policies.list_policies')))

@bp.route('/bulk_upload', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def bulk_upload_policies():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se ha seleccionado ningún archivo', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No se ha seleccionado ningún archivo', 'error')
            return redirect(request.url)
            
        if file and file.filename.endswith('.xlsx'):
            error_details = []
            updated_count = 0
            created_count = 0
            error_count = 0
            
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join('/tmp', filename)
                file.save(file_path)
                
                workbook = openpyxl.load_workbook(file_path)
                sheet = workbook.active
                
                for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
                    try:
                        policy_number, start_date, end_date, premium, client_document_number, product_name, agent_document_number, emision_status, payment_status = row
                        
                        client = Client.query.filter_by(document_number=client_document_number).first()
                        product = Product.query.filter_by(name=product_name).first()
                        agent = User.query.filter_by(document_number=agent_document_number, role=UserRole.AGENTE).first()
                        
                        if not all([client, product, agent]):
                            missing = []
                            if not client: missing.append("Cliente")
                            if not product: missing.append("Producto")
                            if not agent: missing.append("Agente")
                            raise ValueError(f"Datos faltantes: {', '.join(missing)}")
                        
                        try:
                            premium_decimal = Decimal(str(premium))
                        except InvalidOperation:
                            raise ValueError(f"Valor de prima inválido: {premium}")
                        
                        # Usar dateutil.parser para analizar fechas
                        start_date_parsed = parser.parse(start_date).date()
                        end_date_parsed = parser.parse(end_date).date()
                        
                        existing_policy = Policy.query.filter_by(policy_number=policy_number).first()
                        if existing_policy:
                            existing_policy.start_date = start_date_parsed
                            existing_policy.end_date = end_date_parsed
                            existing_policy.premium = float(premium_decimal)
                            existing_policy.client_id = client.id
                            existing_policy.product_id = product.id
                            existing_policy.agent_id = agent.id
                            existing_policy.emision_status = EmisionStatus[emision_status.upper()]
                            existing_policy.payment_status = PaymentStatus[payment_status.upper()]
                            updated_count += 1
                            logging.info(f'Póliza {policy_number} actualizada exitosamente. Prima: {premium_decimal}')
                        else:
                            policy = Policy(
                                policy_number=policy_number,
                                start_date=start_date_parsed,
                                end_date=end_date_parsed,
                                premium=float(premium_decimal),
                                client_id=client.id,
                                product_id=product.id,
                                agent_id=agent.id,
                                emision_status=EmisionStatus[emision_status.upper()],
                                payment_status=PaymentStatus[payment_status.upper()]
                            )
                            db.session.add(policy)
                            created_count += 1
                            logging.info(f'Póliza {policy_number} creada exitosamente. Prima: {premium_decimal}')
                    except Exception as e:
                        error_count += 1
                        error_details.append({
                            'row': idx,
                            'message': str(e),
                            'data': ', '.join([str(cell) for cell in row if cell])
                        })
                
                # Hacer commit antes de enviar el mensaje flash
                db.session.commit()
                
                # Enviar el mensaje flash después del commit
                if error_details:
                    return render_template('policies/bulk_upload.html', 
                        summary={
                            'updated': updated_count,
                            'created': created_count,
                            'errors': error_count,
                            'error_details': error_details
                        })
                else:
                    flash(f'Carga masiva completada exitosamente. Actualizadas: {updated_count}, Creadas: {created_count}')
                    return redirect(url_for('policies.list_policies'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error al procesar el archivo: {str(e)}', 'error')
            
        else:
            flash('Formato de archivo inválido. Por favor, suba un archivo XLSX.', 'error')
            
    return render_template('policies/bulk_upload.html')

@bp.route('/download_sample')
@login_required
@admin_or_digitador_required
def download_policy_sample():
    return send_file('static/samples/polizas_ejemplo.xlsx', as_attachment=True)

@bp.route('/search_clients')
@login_required
@admin_or_digitador_required
def search_clients():
    query = request.args.get('query', '')
    clients = Client.query.filter(Client.name.ilike(f'%{query}%')).limit(10).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in clients])

@bp.route('/search_agents')
@login_required
@admin_or_digitador_required
def search_agents():
    query = request.args.get('query', '')
    agents = User.query.filter(
        User.role == UserRole.AGENTE,
        User.name.ilike(f'%{query}%')
    ).limit(10).all()
    return jsonify([{
        'id': a.id, 
        'name': f"{a.name} ({a.document_number})"
    } for a in agents])

@bp.route('/<int:id>')
@login_required
@admin_or_digitador_or_agent_required
def policy_detail(id):
    """Vista detallada de una póliza."""
    policy = Policy.query.get_or_404(id)
    
    # Verificar si el usuario actual es un agente y si la póliza le pertenece
    if current_user.role == UserRole.AGENTE and policy.agent_id != current_user.id:
        abort(403)  # Forbidden
    
    # Calcular comisiones
    commissions = Commission.query.filter_by(policy_id=policy.id).all()
    total_commission = sum(float(commission.amount) for commission in commissions)
    
    return render_template(
        'policies/detail.html',
        policy=policy,
        commissions=commissions,
        total_commission=total_commission
    )

@bp.route('/recalculate_commission/<int:id>')
@login_required
@admin_required
def recalculate_commission(id):
    try:
        policy = Policy.query.get_or_404(id)
        
        # Eliminar comisiones existentes
        Commission.query.filter_by(policy_id=policy.id).delete()
        
        # Recalcular comisiones
        agent = User.query.get(policy.agent_id)
        commission = agent.calculate_commission(policy)
        
        if commission:
            db.session.commit()
            flash('Comisiones recalculadas exitosamente.', 'success')
        else:
            flash('No se pudieron calcular las comisiones.', 'error')
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al recalcular comisiones: {str(e)}")
        flash(f'Error al recalcular comisiones: {str(e)}', 'error')
    
    return redirect(get_return_url(url_for('policies.policy_detail', id=id)))

