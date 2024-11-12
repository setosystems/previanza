from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required
from models import Client, Policy, User, db, DocumentType, UserRole
from forms import ClientForm
from decorators import admin_required, admin_or_digitador_required
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
    name = request.args.get('name', '')
    email = request.args.get('email', '')
    document_type = request.args.get('document_type', '')
    policy_number = request.args.get('policy_number', '')
    agent_name = request.args.get('agent_name', '')
    
    query = Client.query
    if name:
        query = query.filter(Client.name.ilike(f'%{name}%'))
    if email:
        query = query.filter(Client.email.ilike(f'%{email}%'))
    if document_type:
        query = query.filter(Client.document_type == DocumentType[document_type])
    if policy_number:
        query = query.join(Policy).filter(Policy.policy_number.ilike(f'%{policy_number}%'))
    if agent_name:
        query = query.join(Policy).join(User, Policy.agent_id == User.id).filter(
            or_(User.username.ilike(f'%{agent_name}%'), User.name.ilike(f'%{agent_name}%'))
        )
    
    # Añadir paginación
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de clientes por página
    clients = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('clients/list.html', clients=clients.items, document_types=DocumentType, pagination=clients)

    #clients = query.all()
    #return render_template('clients/list.html', clients=clients, document_types=DocumentType)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def create_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            document_type=DocumentType[form.document_type.data],
            document_number=form.document_number.data,
            birthdate=form.birthdate.data
        )
        db.session.add(client)
        db.session.commit()
        flash('Cliente creado exitosamente.')
        return redirect(url_for('clients.list_clients'))
    return render_template('clients/create.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        form.populate_obj(client)
        client.document_type = DocumentType[form.document_type.data]
        db.session.commit()
        flash('Cliente actualizado exitosamente.')
        return redirect(url_for('clients.list_clients'))
    return render_template('clients/edit.html', form=form, client=client)

@bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_client(id):
    client = Client.query.get_or_404(id)
    
    associated_policies = Policy.query.filter_by(client_id=client.id).first()
    
    if associated_policies:
        flash('No se puede eliminar el cliente porque tiene pólizas asociadas. Por favor, elimine primero las pólizas asociadas.', 'error')
        return redirect(url_for('clients.list_clients'))
    
    try:
        db.session.delete(client)
        db.session.commit()
        flash('Cliente eliminado exitosamente.', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('No se pudo eliminar el cliente debido a restricciones de integridad de la base de datos.', 'error')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al eliminar el cliente: {str(e)}")
        flash('Ocurrió un error al intentar eliminar el cliente.', 'error')
    
    return redirect(url_for('clients.list_clients'))

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
                        })
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
            
    return render_template('clients/bulk_upload.html')

@bp.route('/download_sample')
@login_required
@admin_or_digitador_required
def download_client_sample():
    return send_file('static/samples/clientes_ejemplo.xlsx', as_attachment=True)

@bp.route('/detail/<int:id>')
@login_required
@admin_or_digitador_required
def client_detail(id):
    client = Client.query.get_or_404(id)
    policies = Policy.query.filter_by(client_id=client.id).all()
    return render_template('clients/detail.html', client=client, policies=policies)
