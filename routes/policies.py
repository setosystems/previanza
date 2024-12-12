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
    form.product_id.choices = [(p.id, p.name) for p in Product.query.all()]
    
    if form.validate_on_submit():
        client = Client.query.get(form.client_id.data)
        agent = User.query.get(form.agent_id.data)
        if not client or not agent:
            flash('Cliente o agente no válido', 'error')
            return render_template('policies/create.html', form=form)
        
        try:
            # Verificar si ya existe una póliza con ese número
            existing_policy = Policy.query.filter_by(policy_number=form.policy_number.data).first()
            if existing_policy:
                flash(f'Ya existe una póliza con el número {form.policy_number.data}. Por favor, utilice un número diferente.', 'error')
                return render_template('policies/create.html', form=form)

            # Crear la póliza
            policy = Policy(
                policy_number=form.policy_number.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                premium=form.premium.data,
                client_id=client.id,
                product_id=form.product_id.data,
                agent_id=agent.id,
                emision_status=EmisionStatus[form.emision_status.data.upper()],
                payment_status=PaymentStatus[form.payment_status.data.upper()]
            )
            db.session.add(policy)
            db.session.flush()

            # Calcular y registrar las comisiones
            agent.calculate_commission(policy)
            
            db.session.commit()
            flash('Póliza creada exitosamente.', 'success')
            return redirect(url_for('policies.list_policies'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error al crear póliza: {str(e)}")
            
            # Manejo específico de errores comunes
            if isinstance(e, sqlalchemy.exc.IntegrityError):
                if 'policy_policy_number_key' in str(e):
                    flash(f'Ya existe una póliza con el número {form.policy_number.data}. Por favor, utilice un número diferente.', 'error')
                else:
                    flash('Error de integridad en los datos. Por favor, verifique la información ingresada.', 'error')
            else:
                flash('Ha ocurrido un error inesperado. Por favor, intente nuevamente o contacte al administrador.', 'error')
            
    return render_template('policies/create.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def edit_policy(id):
    policy = Policy.query.get_or_404(id)
    form = PolicyForm(obj=policy)
    form.product_id.choices = [(p.id, p.name) for p in Product.query.all()]
    
    if form.validate_on_submit():
        try:
            old_payment_status = policy.payment_status
            new_payment_status = PaymentStatus[form.payment_status.data.upper()]
            
            # Actualizar la póliza
            policy.policy_number = form.policy_number.data
            policy.start_date = form.start_date.data
            policy.end_date = form.end_date.data
            policy.premium = form.premium.data
            policy.client_id = form.client_id.data
            policy.product_id = form.product_id.data
            policy.agent_id = form.agent_id.data
            policy.emision_status = EmisionStatus[form.emision_status.data.upper()]
            policy.payment_status = new_payment_status
            
            # Forzar el cálculo de comisiones si el estado cambia a PAGADO
            if old_payment_status != PaymentStatus.PAGADO and new_payment_status == PaymentStatus.PAGADO:
                logging.info(f"Calculando comisiones para póliza {policy.policy_number} debido a cambio de estado a PAGADO")
                agent = User.query.get(policy.agent_id)
                agent.calculate_commission(policy)
            
            db.session.commit()
            flash('Póliza actualizada exitosamente.', 'success')
            return redirect(url_for('policies.list_policies'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f'Error al editar la póliza {id}: {str(e)}', exc_info=True)
            flash(f'Ocurrió un error al editar la póliza: {str(e)}', 'error')
    
    # Establecer los valores actuales en el formulario
    form.client.data = policy.client.name
    form.agent.data = f"{policy.agent.name} ({policy.agent.document_number})"
    form.emision_status.data = policy.emision_status.name
    form.payment_status.data = policy.payment_status.name
    
    return render_template('policies/edit.html', form=form, policy=policy)

@bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_policy(id):
    try:
        policy = Policy.query.get_or_404(id)
        db.session.delete(policy)
        db.session.commit()
        flash('Póliza eliminada exitosamente.', 'success')
    except OperationalError as oe:
        db.session.rollback()
        logging.error(f'Error de operación al eliminar la póliza {id}: {str(oe)}')
        flash('Ocurrió un error al eliminar la póliza. Por favor, intenta de nuevo.', 'error')
    except Exception as e:
        db.session.rollback()
        logging.error(f'Error inesperado al eliminar la póliza {id}: {str(e)}')
        flash('Ocurrió un error inesperado. Por favor, contacta al administrador.', 'error')
    return redirect(url_for('policies.list_policies'))

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
        
    return redirect(url_for('policies.policy_detail', id=id))

