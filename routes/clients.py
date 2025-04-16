from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, session
from flask_login import login_required
from models import Client, Policy, User, db, DocumentType, UserRole
from forms import ClientForm
from decorators import admin_required, admin_or_digitador_required
from utils.url_helpers import get_return_url
from werkzeug.utils import secure_filename
import openpyxl
import os
from datetime import datetime
from dateutil import parser
import logging
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

bp = Blueprint('clients', __name__, url_prefix='/clients')

@bp.route('/')
@login_required
@admin_or_digitador_required
def list_clients():
    # Hacer la sesión permanente al entrar a esta vista
    session.permanent = True
    
    # Guardar/recuperar parámetros de paginación, filtros y ordenamiento en la sesión
    session_key = 'clients_list_params'
    
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
            'document_type': request.args.get('document_type', ''),
            'document': request.args.get('document', ''),
            'birthdate_from': request.args.get('birthdate_from', ''),
            'birthdate_to': request.args.get('birthdate_to', ''),
            'sort_by': request.args.get('sort_by', 'name'),
            'sort_order': request.args.get('sort_order', 'asc'),
            'page': request.args.get('page', 1, type=int),
            'per_page': request.args.get('per_page', 10, type=int)
        }
    
    # Si no hay parámetros pero sí hay sesión guardada, recuperarla para mantener el estado
    elif session_key in session:
        return redirect(url_for('clients.list_clients', **session[session_key]))
    
    # Obtener los parámetros ya sea de la solicitud o de la sesión
    params = session.get(session_key, {})
    name = params.get('name', request.args.get('name', ''))
    email = params.get('email', request.args.get('email', ''))
    document_type = params.get('document_type', request.args.get('document_type', ''))
    document_number = params.get('document', request.args.get('document', ''))
    birthdate_from = params.get('birthdate_from', request.args.get('birthdate_from', ''))
    birthdate_to = params.get('birthdate_to', request.args.get('birthdate_to', ''))
    
    # Parámetros de ordenamiento
    sort_by = params.get('sort_by', request.args.get('sort_by', 'name'))
    sort_order = params.get('sort_order', request.args.get('sort_order', 'asc'))
    
    # Mapeo de nombres de parámetros a atributos de modelo para ordenamiento
    sort_columns = {
        'name': Client.name,
        'email': Client.email,
        'document_number': Client.document_number,
        'city': Client.city,
        'birthdate': Client.birthdate
    }
    
    query = Client.query
    if name:
        query = query.filter(Client.name.ilike(f'%{name}%'))
    if email:
        query = query.filter(Client.email.ilike(f'%{email}%'))
    if document_type:
        query = query.filter(Client.document_type == DocumentType[document_type])
    if document_number:
        query = query.filter(Client.document_number.ilike(f'%{document_number}%'))
    
    # Filtro por rango de fechas de nacimiento
    if birthdate_from:
        try:
            from_date = datetime.strptime(birthdate_from, '%Y-%m-%d').date()
            query = query.filter(Client.birthdate >= from_date)
        except ValueError:
            flash('Formato de fecha inicial inválido. Use YYYY-MM-DD', 'warning')
    
    if birthdate_to:
        try:
            to_date = datetime.strptime(birthdate_to, '%Y-%m-%d').date()
            query = query.filter(Client.birthdate <= to_date)
        except ValueError:
            flash('Formato de fecha final inválido. Use YYYY-MM-DD', 'warning')
    
    # Aplicar ordenamiento
    if sort_by in sort_columns:
        if sort_order == 'desc':
            query = query.order_by(sort_columns[sort_by].desc())
        else:
            query = query.order_by(sort_columns[sort_by].asc())
    else:
        # Ordenamiento por defecto
        query = query.order_by(Client.name)
    
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
    
    return render_template('clients/list.html', 
                         clients=pagination.items, 
                         document_types=DocumentType, 
                         pagination=pagination,
                         title="Lista de Clientes",
                         sort_by=sort_by,
                         sort_order=sort_order,
                         birthdate_from=birthdate_from,
                         birthdate_to=birthdate_to,
                         show_client_actions=True)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def create_client():
    form = ClientForm()
    if form.validate_on_submit():
        try:
            # Crear el cliente sin usar populate_obj
            client = Client(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
                city=form.city.data,
                document_number=form.document_number.data,
                birthdate=form.birthdate.data
            )
            
            # Convertir explícitamente el tipo de documento de texto a enum
            if form.document_type.data:
                try:
                    client.document_type = DocumentType[form.document_type.data]
                except KeyError:
                    flash(f'Tipo de documento inválido: {form.document_type.data}', 'error')
                    return render_template('clients/create.html', form=form)
            
            db.session.add(client)
            db.session.commit()
            flash('Cliente creado exitosamente', 'success')
            return redirect(get_return_url(url_for('clients.list_clients')))
        except IntegrityError:
            db.session.rollback()
            flash('Error: Ya existe un cliente con ese número de documento', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el cliente: {str(e)}', 'error')
            logging.error(f"Error al crear cliente: {str(e)}")
    
    return render_template('clients/create.html', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    # Establecer el ID del cliente para la validación
    form.id.data = str(client.id)
    
    if form.validate_on_submit():
        try:
            # Actualizar los campos manualmente en lugar de usar populate_obj
            client.name = form.name.data
            client.email = form.email.data
            client.phone = form.phone.data
            client.address = form.address.data
            client.city = form.city.data
            client.document_number = form.document_number.data
            client.birthdate = form.birthdate.data
            
            # Convertir explícitamente el tipo de documento de texto a enum
            if form.document_type.data:
                try:
                    client.document_type = DocumentType[form.document_type.data]
                except KeyError:
                    flash(f'Tipo de documento inválido: {form.document_type.data}', 'error')
                    return render_template('clients/edit.html', form=form, client=client)
            
            db.session.commit()
            flash('Cliente actualizado exitosamente', 'success')
            return redirect(get_return_url(url_for('clients.list_clients')))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el cliente: {str(e)}', 'error')
            logging.error(f"Error al actualizar cliente: {str(e)}")
    
    return render_template('clients/edit.html', form=form, client=client)

@bp.route('/delete/<int:id>')
@login_required
@admin_or_digitador_required
def delete_client(id):
    client = Client.query.get_or_404(id)
    try:
        db.session.delete(client)
        db.session.commit()
        flash('Cliente eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el cliente: {str(e)}', 'error')
    
    return redirect(get_return_url(url_for('clients.list_clients')))

@bp.route('/bulk_upload', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def bulk_upload_clients():
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
                        name, email, phone, address, city, document_type, document_number, birthdate = row
                        
                        name = str(name).strip() if name else None
                        email = str(email).strip().lower() if email else None
                        phone = str(phone).strip() if phone else None
                        address = str(address).strip() if address else None
                        city = str(city).strip() if city else None
                        document_type = str(document_type).strip().upper() if document_type else None
                        document_number = str(document_number).strip() if document_number else None
                        
                        if not email:
                            raise ValueError("El correo electrónico es obligatorio")
                        
                        if document_type and document_type not in [dt.name for dt in DocumentType]:
                            raise ValueError(f"El tipo de documento '{document_type}' no es válido")
                        
                        try:
                            birthdate = parser.parse(str(birthdate)).date() if birthdate else None
                        except ValueError:
                            raise ValueError(f"El formato de fecha de nacimiento '{birthdate}' no es válido. Use YYYY-MM-DD")
                        
                        # Verificar si ya existe un cliente con el mismo documento
                        existing_client_doc = Client.query.filter_by(
                            document_type=DocumentType[document_type] if document_type else None,
                            document_number=document_number
                        ).first()
                        
                        if existing_client_doc:
                            raise ValueError(f"Ya existe un cliente con el documento {document_type}: {document_number}")
                        
                        existing_client = Client.query.filter_by(email=email).first()
                        if existing_client:
                            existing_client.name = name
                            existing_client.phone = phone
                            existing_client.address = address
                            existing_client.city = city
                            existing_client.document_type = DocumentType[document_type] if document_type else None
                            existing_client.document_number = document_number
                            existing_client.birthdate = birthdate
                            updated_count += 1
                        else:
                            new_client = Client(
                                name=name,
                                email=email,
                                phone=phone,
                                address=address,
                                city=city,
                                document_type=DocumentType[document_type] if document_type else None,
                                document_number=document_number,
                                birthdate=birthdate
                            )
                            db.session.add(new_client)
                            created_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        # Traducir mensajes de error comunes
                        error_message = str(e)
                        if "too many values to unpack" in error_message:
                            error_message = "Número incorrecto de columnas en la fila. Asegúrese de tener exactamente 8 columnas"
                        elif "invalid literal for int()" in error_message:
                            error_message = "Valor numérico inválido"
                        elif "does not match format" in error_message:
                            error_message = "Formato de fecha inválido. Use YYYY-MM-DD"
                        elif "not enough values to unpack" in error_message:
                            error_message = "Faltan columnas en la fila. Asegúrese de tener todas las columnas requeridas"
                        
                        error_details.append({
                            'row': idx,
                            'message': error_message,
                            'data': ', '.join([str(cell) for cell in row if cell])
                        })
                
                db.session.commit()
                
                if error_details:
                    return render_template('clients/bulk_upload.html', 
                        summary={
                            'updated': updated_count,
                            'created': created_count,
                            'errors': error_count,
                            'error_details': error_details
                        },
                        title="Carga Masiva de Clientes")
                else:
                    flash(f'Carga masiva completada exitosamente. Actualizados: {updated_count}, Creados: {created_count}')
                    return redirect(url_for('clients.list_clients'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error al procesar el archivo: {str(e)}', 'error')
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
        else:
            flash('Formato de archivo inválido. Por favor, suba un archivo XLSX.', 'error')
            
    return render_template('clients/bulk_upload.html', title="Carga Masiva de Clientes")

@bp.route('/download_sample')
@login_required
@admin_or_digitador_required
def download_client_sample():
    return send_file('static/samples/clientes_ejemplo.xlsx', as_attachment=True)

@bp.route('/detail/<int:id>')
@login_required
@admin_or_digitador_required
def client_detail(id):
    try:
        client = Client.query.get_or_404(id)
        policies = Policy.query.filter_by(client_id=client.id)\
            .order_by(Policy.start_date.desc())\
            .all()
        
        return render_template('clients/detail.html', 
                             client=client, 
                             policies=policies,
                             document_types=DocumentType,
                             title=f"Cliente: {client.name}")
    except Exception as e:
        logging.error(f"Error al mostrar detalle del cliente {id}: {str(e)}")
        flash('Error al cargar los detalles del cliente.', 'error')
        return redirect(url_for('clients.list_clients'))
