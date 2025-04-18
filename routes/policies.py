from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, jsonify, abort, session
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
from sqlalchemy import or_

bp = Blueprint('policies', __name__, url_prefix='/policies')

@bp.route('/')
@login_required
@admin_or_digitador_or_agent_required
def list_policies():
    # Hacer la sesión permanente al entrar a esta vista
    session.permanent = True
    
    # Guardar/recuperar parámetros de paginación, filtros y ordenamiento en la sesión
    session_key = 'policies_list_params'
    
    # Si hay parámetros en la solicitud, actualizar la sesión
    if request.args:
        # Limpiar la sesión si se hace una nueva búsqueda (cuando hay parámetros pero no hay page)
        if ('policy_number' in request.args or 'client_name' in request.args or 'product_name' in request.args) and 'page' not in request.args:
            if session_key in session:
                session.pop(session_key)
                
        # Guardar los parámetros actuales en la sesión
        session[session_key] = {
            'policy_number': request.args.get('policy_number', ''),
            'client_id': request.args.get('client_id', ''),
            'client_name': request.args.get('client_name', ''),
            'product_id': request.args.get('product_id', ''),
            'product_name': request.args.get('product_name', ''),
            'agent_id': request.args.get('agent_id', ''),
            'agent_name': request.args.get('agent_name', ''),
            'status': request.args.get('status', ''),
            'payment_status': request.args.get('payment_status', ''),
            'emision_status': request.args.get('emision_status', ''),
            'sort_by': request.args.get('sort_by', 'start_date'),
            'sort_order': request.args.get('sort_order', 'desc'),
            'page': request.args.get('page', 1, type=int),
            'per_page': request.args.get('per_page', 10, type=int)
        }
    
    # Si no hay parámetros pero sí hay sesión guardada, recuperarla para mantener el estado
    elif session_key in session:
        return redirect(url_for('policies.list_policies', **session[session_key]))
    
    # Obtener los parámetros ya sea de la solicitud o de la sesión
    params = session.get(session_key, {})
    policy_number = params.get('policy_number', request.args.get('policy_number', ''))
    client_id = params.get('client_id', request.args.get('client_id', ''))
    client_name = params.get('client_name', request.args.get('client_name', ''))
    product_id = params.get('product_id', request.args.get('product_id', ''))
    product_name = params.get('product_name', request.args.get('product_name', ''))
    agent_id = params.get('agent_id', request.args.get('agent_id', ''))
    agent_name = params.get('agent_name', request.args.get('agent_name', ''))
    status = params.get('status', request.args.get('status', ''))
    payment_status = params.get('payment_status', request.args.get('payment_status', ''))
    emision_status = params.get('emision_status', request.args.get('emision_status', ''))
    
    # Parámetros de ordenamiento
    sort_by = params.get('sort_by', request.args.get('sort_by', 'start_date'))
    sort_order = params.get('sort_order', request.args.get('sort_order', 'desc'))
    
    # Mapeo de nombres de parámetros a atributos de modelo para ordenamiento
    sort_columns = {
        'policy_number': Policy.policy_number,
        'client': Client.name,
        'product': Product.name,
        'premium': Policy.premium,
        'start_date': Policy.start_date,
        'end_date': Policy.end_date,
        'agent': User.name
    }
    
    # Aplicar joins para filtrado y ordenamiento
    query = Policy.query
    
    # Siempre aplicamos los joins aquí para poder filtrar por relaciones
    query = query.join(Client, Policy.client_id == Client.id)
    query = query.join(Product, Policy.product_id == Product.id)
    query = query.join(User, Policy.agent_id == User.id)
    
    # Aplicar filtros
    if policy_number:
        query = query.filter(Policy.policy_number.ilike(f'%{policy_number}%'))
    
    # Filtrado de cliente (por ID o por nombre)
    if client_id:
        query = query.filter(Policy.client_id == client_id)
    elif client_name:
        query = query.filter(Client.name.ilike(f'%{client_name}%'))
    
    # Filtrado de producto (por ID o por nombre)
    if product_id:
        query = query.filter(Policy.product_id == product_id)
    elif product_name:
        query = query.filter(Product.name.ilike(f'%{product_name}%'))
    
    # Filtrado de agente (por ID o por nombre)
    if agent_id:
        query = query.filter(Policy.agent_id == agent_id)
    elif agent_name:
        query = query.filter(User.name.ilike(f'%{agent_name}%'))
    
    if status:
        query = query.filter(Policy.status == status)
    if payment_status:
        query = query.filter(Policy.payment_status == payment_status)
    if emision_status:
        query = query.filter(Policy.emision_status == emision_status)
    
    # Aplicar ordenamiento
    if sort_by in sort_columns:
        if sort_order == 'desc':
            query = query.order_by(sort_columns[sort_by].desc())
        else:
            query = query.order_by(sort_columns[sort_by].asc())
    else:
        query = query.order_by(Policy.start_date.desc())
    
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
    
    return render_template('policies/list.html', 
                          policies=pagination.items, 
                          pagination=pagination,
                          clients=Client.query.all(),
                          products=Product.query.all(),
                          agents=User.query.filter_by(role=UserRole.AGENTE).all(),
                          title="Lista de Pólizas",
                          sort_by=sort_by,
                          sort_order=sort_order,
                          EmisionStatus=EmisionStatus,
                          PaymentStatus=PaymentStatus,
                          client_id=client_id,
                          client_name=client_name,
                          product_id=product_id,
                          product_name=product_name,
                          agent_id=agent_id,
                          agent_name=agent_name)

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
            all_error_details = []
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
                    # Iniciar una nueva transacción para cada fila
                    try:
                        # Verificar si hay 10 columnas (incluyendo solicitation_date)
                        if len(row) >= 10:
                            policy_number, start_date, end_date, premium, client_document_number, product_name, agent_document_number, emision_status, payment_status, solicitation_date = row[:10]
                        else:
                            # Formato anterior con 9 columnas
                            policy_number, start_date, end_date, premium, client_document_number, product_name, agent_document_number, emision_status, payment_status = row[:9]
                            solicitation_date = None
                        
                        # Log para depuración
                        logging.info(f"Procesando fila {idx}: {row}")
                        
                        # Verificar si los datos están presentes
                        if not all([policy_number, client_document_number, product_name, agent_document_number]):
                            raise ValueError("Faltan datos obligatorios (número de póliza, documento del cliente, producto o agente)")
                        
                        # Convertir a string si no lo es
                        if client_document_number is not None and not isinstance(client_document_number, str):
                            client_document_number = str(int(client_document_number))
                        
                        if agent_document_number is not None and not isinstance(agent_document_number, str):
                            agent_document_number = str(int(agent_document_number))
                        
                        # Buscar cliente, producto y agente
                        client = Client.query.filter_by(document_number=client_document_number).first()
                        if not client:
                            raise ValueError(f"Cliente con documento {client_document_number} no encontrado")
                        
                        product = Product.query.filter_by(name=product_name).first()
                        if not product:
                            raise ValueError(f"Producto '{product_name}' no encontrado")
                        
                        agent = User.query.filter_by(document_number=agent_document_number, role=UserRole.AGENTE).first()
                        if not agent:
                            raise ValueError(f"Agente con documento {agent_document_number} no encontrado")
                        
                        try:
                            premium_decimal = Decimal(str(premium))
                        except InvalidOperation:
                            raise ValueError(f"Valor de prima inválido: {premium}")
                        
                        # Usar dateutil.parser para analizar fechas
                        try:
                            # Verificar si las fechas ya son objetos date o datetime
                            if isinstance(start_date, (datetime, date)):
                                start_date_parsed = start_date.date() if isinstance(start_date, datetime) else start_date
                            else:
                                start_date_parsed = parser.parse(str(start_date)).date()
                                
                            if isinstance(end_date, (datetime, date)):
                                end_date_parsed = end_date.date() if isinstance(end_date, datetime) else end_date
                            else:
                                end_date_parsed = parser.parse(str(end_date)).date()
                        except Exception as e:
                            raise ValueError(f"Error al procesar las fechas: {str(e)}")
                        
                        # Procesar fecha de solicitud si existe
                        solicitation_date_parsed = None
                        if solicitation_date:
                            try:
                                if isinstance(solicitation_date, (datetime, date)):
                                    solicitation_date_parsed = solicitation_date.date() if isinstance(solicitation_date, datetime) else solicitation_date
                                else:
                                    solicitation_date_parsed = parser.parse(str(solicitation_date)).date()
                            except:
                                logging.warning(f"Fecha de solicitud inválida en fila {idx}: {solicitation_date}")
                        
                        # Procesar estado de emisión
                        try:
                            # Mapeo para valores que existen en el modelo pero no en la base de datos
                            emision_status_map = {
                                'REQ': 'PENDIENTE',            # Mapear REQ a PENDIENTE
                                'REENVIADA': 'PENDIENTE',      # Mapear REENVIADA a PENDIENTE
                                'req': 'PENDIENTE',            # Versión en minúsculas
                                'reenviada': 'PENDIENTE',      # Versión en minúsculas
                                'Req': 'PENDIENTE',            # Versión mixta
                                'Reenviada': 'PENDIENTE',      # Versión mixta
                            }
                            
                            # Normalizar a mayúsculas
                            emision_status_upper = emision_status.upper()
                            
                            # Si necesita mapeo, hacer la conversión
                            if emision_status_upper in emision_status_map:
                                emision_status_upper = emision_status_map[emision_status_upper]
                                logging.info(f"Estado de emisión mapeado: '{emision_status}' -> {emision_status_upper}")
                            
                            # Ahora buscar el enum por nombre
                            try:
                                emision_status_enum = EmisionStatus[emision_status_upper]
                                logging.info(f"Estado de emisión encontrado: {emision_status_enum.name}")
                            except KeyError:
                                # Si no se encuentra, usar PENDIENTE por defecto
                                logging.warning(f"Estado de emisión no encontrado: '{emision_status}', usando PENDIENTE")
                                emision_status_enum = EmisionStatus.PENDIENTE
                                
                        except Exception as e:
                            logging.error(f"Error procesando estado de emisión: {str(e)}")
                            # En caso de error, usar PENDIENTE como fallback
                            emision_status_enum = EmisionStatus.PENDIENTE
                            logging.warning(f"Usando valor fallback PENDIENTE para '{emision_status}'")
                            
                        logging.info(f"Estado de emisión final: {emision_status_enum.name}")
                        
                        # Procesar estado de pago
                        try:
                            payment_status_enum = PaymentStatus[payment_status.upper()]
                        except KeyError:
                            # Intentar buscar por valor
                            try:
                                found = False
                                for status in PaymentStatus:
                                    if status.value.upper() == payment_status.upper():
                                        payment_status_enum = status
                                        logging.info(f"Estado de pago mapeado: '{payment_status}' -> {status.name}")
                                        found = True
                                        break
                                if not found:
                                    valid_states = [f"{p.name} ({p.value})" for p in PaymentStatus]
                                    raise ValueError(f"Estado de pago no válido: '{payment_status}'. Estados válidos: {', '.join(valid_states)}")
                            except Exception as e:
                                raise ValueError(f"Estado de pago no válido: '{payment_status}'. Error: {str(e)}")
                        
                        # Comprobar si la póliza existe - usar una nueva transacción interna
                        try:
                            # Inicio de transacción independiente
                            # Asegurarse de que policy_number sea un string
                            if not isinstance(policy_number, str):
                                policy_number = str(policy_number)
                                
                            existing_policy = Policy.query.filter_by(policy_number=policy_number).first()
                            if existing_policy:
                                existing_policy.start_date = start_date_parsed
                                existing_policy.end_date = end_date_parsed
                                existing_policy.premium = float(premium_decimal)
                                existing_policy.client_id = client.id
                                existing_policy.product_id = product.id
                                existing_policy.agent_id = agent.id
                                existing_policy.emision_status = emision_status_enum
                                existing_policy.payment_status = payment_status_enum
                                existing_policy.solicitation_date = solicitation_date_parsed
                                db.session.commit()
                                updated_count += 1
                                logging.info(f'Póliza {policy_number} actualizada exitosamente.')
                            else:
                                policy = Policy(
                                    policy_number=policy_number,
                                    start_date=start_date_parsed,
                                    end_date=end_date_parsed,
                                    premium=float(premium_decimal),
                                    client_id=client.id,
                                    product_id=product.id,
                                    agent_id=agent.id,
                                    emision_status=emision_status_enum,
                                    payment_status=payment_status_enum,
                                    solicitation_date=solicitation_date_parsed
                                )
                                db.session.add(policy)
                                db.session.commit()
                                created_count += 1
                                logging.info(f'Póliza {policy_number} creada exitosamente.')
                        except Exception as e:
                            db.session.rollback()
                            raise e
                    
                    except Exception as e:
                        # Aseguramos que la transacción se revierte si hay un error
                        db.session.rollback()
                        error_count += 1
                        error_info = {
                            'row': idx,
                            'message': str(e),
                            'data': ', '.join([str(cell) for cell in row if cell is not None])
                        }
                        all_error_details.append(error_info)
                        logging.error(f"Error en fila {idx}: {str(e)}")
                
                # Enviar el mensaje flash después del commit
                if created_count > 0 or updated_count > 0 or error_count > 0:
                    return render_template('policies/bulk_upload.html', 
                        summary={
                            'updated': updated_count,
                            'created': created_count,
                            'errors': error_count,
                            'error_details': all_error_details
                        })
                else:
                    flash('No se procesaron registros. Verifique el formato del archivo.', 'warning')
                    return redirect(url_for('policies.bulk_upload_policies'))
                
            except Exception as e:
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

@bp.route('/search_products')
@login_required
@admin_or_digitador_or_agent_required
def search_products():
    query = request.args.get('query', '')
    products = Product.query.filter(Product.name.ilike(f'%{query}%')).limit(10).all()
    return jsonify([{'id': p.id, 'name': p.name} for p in products])

