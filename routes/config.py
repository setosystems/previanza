from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required
from decorators import admin_required
from models import Product, db, User, UserRole, AgentCommissionOverride, Commission, Policy, SMTPConfig
from forms import ProductForm, SMTPConfigForm
from config import Config
import os
from flask_mail import Message
from extensions import mail
import logging
from smtplib import SMTPException
from sqlalchemy import func
from datetime import datetime, timedelta
from utils.crypto import encrypt_value, decrypt_value

bp = Blueprint('config', __name__, url_prefix='/config')

@bp.route('/')
@login_required
@admin_required
def config_index():
    return render_template('config/index.html')

@bp.route('/smtp', methods=['GET', 'POST'])
@login_required
@admin_required
def smtp_config():
    form = SMTPConfigForm()
    if form.validate_on_submit():
        logging.info("SMTP configuration form submitted")
        
        try:
            # Probar la conexión SMTP antes de guardar
            try:
                test_config = {
                    'MAIL_SERVER': form.mail_server.data,
                    'MAIL_PORT': form.mail_port.data,
                    'MAIL_USE_TLS': form.mail_use_tls.data,
                    'MAIL_USE_SSL': form.mail_use_ssl.data,
                    'MAIL_USERNAME': form.mail_username.data,
                    'MAIL_PASSWORD': form.mail_password.data,
                    'MAIL_DEFAULT_SENDER': form.mail_default_sender.data
                }
                
                # Crear una nueva instancia de Flask-Mail con la configuración de prueba
                test_mail = Mail()
                test_app = current_app._get_current_object()
                test_app.config.update(test_config)
                test_mail.init_app(test_app)
                
                # Intentar enviar un correo de prueba
                msg = Message(
                    'Prueba de Configuración SMTP',
                    sender=form.mail_default_sender.data,
                    recipients=[form.mail_default_sender.data]
                )
                msg.body = 'Esta es una prueba de configuración SMTP.'
                test_mail.send(msg)
                
                # Si llegamos aquí, la prueba fue exitosa
                logging.info("SMTP test successful")
                
                # Desactivar configuración anterior
                SMTPConfig.deactivate_all()
                
                # Crear nueva configuración
                new_config = SMTPConfig(
                    mail_server=form.mail_server.data,
                    mail_port=form.mail_port.data,
                    mail_use_tls=form.mail_use_tls.data,
                    mail_use_ssl=form.mail_use_ssl.data,
                    mail_username=form.mail_username.data,
                    mail_password=encrypt_value(form.mail_password.data),
                    mail_default_sender=form.mail_default_sender.data,
                    is_active=True
                )
                
                db.session.add(new_config)
                db.session.commit()
                
                # Actualizar la configuración de la aplicación
                current_app.config.update(test_config)
                mail.init_app(current_app)
                
                flash('Configuración SMTP verificada y guardada exitosamente.', 'success')
                return redirect(url_for('config.config_index'))
                
            except SMTPException as e:
                logging.error(f"SMTP test failed: {str(e)}")
                flash(f'Error al probar la configuración SMTP: {str(e)}', 'error')
                return render_template('config/smtp.html', form=form)
                
        except Exception as e:
            logging.error(f"Error updating SMTP configuration: {str(e)}")
            flash(f'Error al actualizar la configuración SMTP: {str(e)}', 'error')
            db.session.rollback()
    else:
        # Pre-fill form with current active configuration
        active_config = SMTPConfig.get_active_config()
        if active_config:
            form.mail_server.data = active_config.mail_server
            form.mail_port.data = active_config.mail_port
            form.mail_use_tls.data = active_config.mail_use_tls
            form.mail_use_ssl.data = active_config.mail_use_ssl
            form.mail_username.data = active_config.mail_username
            form.mail_default_sender.data = active_config.mail_default_sender
            # No prellenamos la contraseña por seguridad

    # Display current SMTP configuration (without exposing password)
    active_config = SMTPConfig.get_active_config()
    current_config = None
    if active_config:
        current_config = {
            'MAIL_SERVER': active_config.mail_server,
            'MAIL_PORT': active_config.mail_port,
            'MAIL_USE_TLS': active_config.mail_use_tls,
            'MAIL_USE_SSL': active_config.mail_use_ssl,
            'MAIL_USERNAME': active_config.mail_username,
            'MAIL_DEFAULT_SENDER': active_config.mail_default_sender,
        }

    return render_template('config/smtp.html', form=form, current_config=current_config)

@bp.route('/send_test_email', methods=['POST'])
@login_required
@admin_required
def send_test_email():
    test_email = request.form.get('test_email')
    if not test_email:
        flash('Por favor, proporcione una dirección de correo electrónico válida.', 'error')
        return redirect(url_for('config.smtp_config'))

    try:
        msg = Message('Correo de Prueba',
                      sender=current_app.config['MAIL_DEFAULT_SENDER'],
                      recipients=[test_email])
        msg.body = 'Este es un correo de prueba para verificar la configuración SMTP.'
        
        # Log SMTP configuration details (except password)
        logging.info(f"Attempting to send test email with the following SMTP configuration:")
        logging.info(f"MAIL_SERVER: {current_app.config['MAIL_SERVER']}")
        logging.info(f"MAIL_PORT: {current_app.config['MAIL_PORT']}")
        logging.info(f"MAIL_USE_TLS: {current_app.config['MAIL_USE_TLS']}")
        logging.info(f"MAIL_USE_SSL: {current_app.config['MAIL_USE_SSL']}")
        logging.info(f"MAIL_USERNAME: {current_app.config['MAIL_USERNAME']}")
        logging.info(f"MAIL_DEFAULT_SENDER: {current_app.config['MAIL_DEFAULT_SENDER']}")
        
        mail.send(msg)
        logging.info(f"Test email sent successfully to {test_email}")
        flash('Correo de prueba enviado exitosamente.', 'success')
    except SMTPException as e:
        logging.error(f"SMTP error al enviar correo de prueba: {str(e)}")
        flash(f'Error SMTP al enviar correo de prueba: {str(e)}', 'error')
    except Exception as e:
        logging.error(f"Error inesperado al enviar correo de prueba: {str(e)}")
        flash(f'Error inesperado al enviar correo de prueba: {str(e)}', 'error')

    return redirect(url_for('config.smtp_config'))

@bp.route('/commissions')
@login_required
@admin_required
def commission_settings():
    """Vista principal de configuración de comisiones."""
    products = Product.query.all()
    agents = User.query.filter_by(role=UserRole.AGENTE).all()
    
    # Agregar logs para debug
    logging.debug("Products loaded:")
    for product in products:
        logging.debug(f"Product {product.name}: commission={product.commission_percentage}, override={product.override_percentage}")
    
    logging.debug("Agents loaded:")
    for agent in agents:
        logging.debug(f"Agent {agent.name}:")
        for override in agent.commission_overrides:
            logging.debug(f"  Override for product {override.product.name}: commission={override.commission_percentage}, override={override.override_percentage}")
    
    # Convertir los productos a un formato que podamos usar en JavaScript
    products_data = [{
        'id': p.id,
        'name': p.name,
        'commission_percentage': float(p.commission_percentage),
        'override_percentage': float(p.override_percentage),
        'sobrecomision': p.sobrecomision
    } for p in products]
    
    logging.debug(f"Products data for JS: {products_data}")
    
    return render_template(
        'config/commissions.html',
        products=products,
        agents=agents,
        products_json=products_data
    )

@bp.route('/commissions/product/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def update_product_commission(product_id):
    """Actualiza la comisión estándar y la configuración de sobrecomisión de un producto."""
    product = Product.query.get_or_404(product_id)
    
    try:
        commission_percentage = float(request.form.get('commission_percentage', 0))
        override_percentage = float(request.form.get('override_percentage', 0))
        sobrecomision = request.form.get('sobrecomision', 'false').lower() == 'true'
        
        if not 0 <= commission_percentage <= 100 or not 0 <= override_percentage <= 100:
            return jsonify({
                'status': 'error',
                'message': 'Los porcentajes deben estar entre 0 y 100'
            }), 400
        
        # Actualizar todos los campos del producto
        product.commission_percentage = commission_percentage
        product.override_percentage = override_percentage
        product.sobrecomision = sobrecomision
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Comisión actualizada exitosamente'
        })
    except ValueError:
        return jsonify({
            'status': 'error',
            'message': 'Porcentaje de comisión inválido'
        }), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al actualizar comisión del producto: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error al actualizar la comisión'
        }), 500

@bp.route('/commissions/override', methods=['POST'])
@login_required
@admin_required
def update_agent_commission():
    """Actualiza o crea una comisión personalizada para un agente."""
    try:
        agent_id = int(request.form.get('agent_id'))
        product_id = int(request.form.get('product_id'))
        
        # Manejar valores vacíos
        commission_percentage = request.form.get('commission_percentage', '0')
        override_percentage = request.form.get('override_percentage', '0')
        
        # Convertir a float, usando 0 como valor por defecto si está vacío
        commission_percentage = float(commission_percentage) if commission_percentage.strip() else 0
        override_percentage = float(override_percentage) if override_percentage.strip() else 0
        
        if not 0 <= commission_percentage <= 100 or not 0 <= override_percentage <= 100:
            return jsonify({
                'status': 'error',
                'message': 'Los porcentajes deben estar entre 0 y 100'
            }), 400
        
        override = AgentCommissionOverride.query.filter_by(
            agent_id=agent_id,
            product_id=product_id
        ).first()
        
        if override:
            override.commission_percentage = commission_percentage
            override.override_percentage = override_percentage
        else:
            override = AgentCommissionOverride(
                agent_id=agent_id,
                product_id=product_id,
                commission_percentage=commission_percentage,
                override_percentage=override_percentage
            )
            db.session.add(override)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Comisiones actualizadas exitosamente'
        })
    except ValueError as e:
        db.session.rollback()
        logging.error(f"Error de valor al actualizar comisiones: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Por favor, ingrese valores numéricos válidos para los porcentajes'
        }), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al actualizar comisiones: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error al actualizar las comisiones'
        }), 500

@bp.route('/commissions/override/<int:agent_id>/<int:product_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_agent_commission(agent_id, product_id):
    """Elimina una comisión personalizada."""
    try:
        override = AgentCommissionOverride.query.filter_by(
            agent_id=agent_id,
            product_id=product_id
        ).first()
        
        if override:
            db.session.delete(override)
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': 'Comisión personalizada eliminada exitosamente'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Comisión personalizada no encontrada'
            }), 404
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al eliminar comisión personalizada: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error al eliminar la comisión personalizada'
        }), 500

@bp.route('/commissions/report')
@login_required
@admin_required
def commission_report():
    """Genera un reporte de comisiones."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    agent_id = request.args.get('agent_id')
    
    query = db.session.query(
        User.name.label('agent_name'),
        func.sum(Commission.amount).label('total_commission')
    ).join(Commission, User.id == Commission.agent_id)
    
    if start_date:
        query = query.filter(Commission.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Commission.date <= datetime.strptime(end_date, '%Y-%m-%d'))
    if agent_id:
        query = query.filter(User.id == agent_id)
    
    results = query.group_by(User.name).all()
    
    return render_template(
        'config/commission_report.html',
        results=results,
        start_date=start_date,
        end_date=end_date
    )

@bp.route('/commissions/agent/<int:agent_id>/details')
@login_required
@admin_required
def get_agent_commission_details(agent_id):
    """Obtiene los detalles de comisiones para un agente específico."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = db.session.query(
        Commission,
        Policy,
        Product
    ).join(
        Policy, Commission.policy_id == Policy.id
    ).join(
        Product, Policy.product_id == Product.id
    ).filter(
        Commission.agent_id == agent_id
    )
    
    if start_date:
        query = query.filter(Commission.date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Commission.date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    results = query.all()
    
    details = [{
        'date': result.Commission.date.strftime('%Y-%m-%d'),
        'policy_number': result.Policy.policy_number,
        'product_name': result.Product.name,
        'premium': float(result.Policy.premium),
        'commission': float(result.Commission.amount),
        'commission_type': 'Sobrecomisión' if result.Commission.commission_type == 'override' else 'Directa'
    } for result in results]
    
    return jsonify({'details': details})

@bp.route('/commissions/override/<int:agent_id>/<int:product_id>')
@login_required
@admin_required
def get_agent_commission(agent_id, product_id):
    """Obtiene los valores de comisión personalizada para un agente y producto."""
    override = AgentCommissionOverride.query.filter_by(
        agent_id=agent_id,
        product_id=product_id
    ).first()
    
    if override:
        return jsonify({
            'status': 'success',
            'commission_percentage': float(override.commission_percentage),
            'override_percentage': float(override.override_percentage)
        })
    else:
        return jsonify({
            'status': 'success',
            'commission_percentage': None,
            'override_percentage': None
        })
