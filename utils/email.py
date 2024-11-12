from flask import current_app, render_template_string
from flask_mail import Message
from extensions import mail
import logging
from datetime import datetime

# Plantilla HTML para las notificaciones de comisión
COMMISSION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }
        .content {
            background-color: #f8f9fa;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 0 0 5px 5px;
        }
        .detail-row {
            margin: 10px 0;
        }
        .detail-label {
            font-weight: bold;
            color: #2c3e50;
        }
        .amount {
            color: #b8860b;
            font-weight: bold;
        }
        .footer {
            margin-top: 20px;
            text-align: center;
            font-size: 0.9em;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>{{ title }}</h2>
    </div>
    <div class="content">
        <p>Estimado/a {{ agent_name }},</p>
        
        <p>{{ message_intro }}</p>
        
        <div class="details">
            <div class="detail-row">
                <span class="detail-label">Póliza:</span> 
                <span>{{ policy_number }}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Producto:</span> 
                <span>{{ product_name }}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Prima:</span> 
                <span class="amount">${{ "{:,.2f}".format(premium) }}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">{{ commission_label }}:</span> 
                <span class="amount">${{ "{:,.2f}".format(commission_amount) }}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Porcentaje aplicado:</span> 
                <span>{{ percentage }}%</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Fecha:</span> 
                <span>{{ date }}</span>
            </div>
            {% if child_agent %}
            <div class="detail-row">
                <span class="detail-label">Agente:</span> 
                <span>{{ child_agent }}</span>
            </div>
            {% endif %}
        </div>

        <p>Para ver más detalles, ingrese a su panel de control.</p>
    </div>
    <div class="footer">
        <p>Este es un correo automático, por favor no responda a este mensaje.</p>
        <p>Sistema de Gestión de Comisiones</p>
    </div>
</body>
</html>
"""

def send_commission_notification(agent, commission, policy):
    """
    Envía una notificación por email cuando se registra una nueva comisión.
    """
    try:
        msg = Message(
            'Nueva Comisión Registrada',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[agent.email]
        )
        
        # Preparar los datos para la plantilla
        template_data = {
            'title': 'Nueva Comisión Registrada',
            'agent_name': agent.name,
            'message_intro': 'Se ha registrado una nueva comisión a su favor con los siguientes detalles:',
            'policy_number': policy.policy_number,
            'product_name': policy.product.name,
            'premium': float(policy.premium),
            'commission_amount': float(commission.amount),
            'commission_label': 'Comisión',
            'percentage': float(commission.percentage_applied),
            'date': commission.date.strftime('%d/%m/%Y'),
            'child_agent': None
        }
        
        # Renderizar la plantilla HTML
        msg.html = render_template_string(COMMISSION_EMAIL_TEMPLATE, **template_data)
        
        # Versión texto plano como respaldo
        msg.body = f"""
Estimado/a {agent.name},

Se ha registrado una nueva comisión a su favor con los siguientes detalles:

Póliza: {policy.policy_number}
Producto: {policy.product.name}
Prima: ${policy.premium:,.2f}
Comisión: ${commission.amount:,.2f}
Porcentaje aplicado: {commission.percentage_applied}%
Fecha: {commission.date.strftime('%d/%m/%Y')}

Para ver más detalles, ingrese a su panel de control.

Saludos cordiales,
Sistema de Gestión de Comisiones
"""
        
        mail.send(msg)
        logging.info(f"Notificación de comisión enviada a {agent.email}")
        return True
        
    except Exception as e:
        logging.error(f"Error al enviar notificación de comisión: {str(e)}")
        return False

def send_override_commission_notification(agent, commission, policy, child_agent):
    """
    Envía una notificación por email cuando se registra una sobrecomisión.
    """
    try:
        msg = Message(
            'Nueva Sobrecomisión Registrada',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[agent.email]
        )
        
        # Preparar los datos para la plantilla
        template_data = {
            'title': 'Nueva Sobrecomisión Registrada',
            'agent_name': agent.name,
            'message_intro': 'Se ha registrado una nueva sobrecomisión a su favor con los siguientes detalles:',
            'policy_number': policy.policy_number,
            'product_name': policy.product.name,
            'premium': float(policy.premium),
            'commission_amount': float(commission.amount),
            'commission_label': 'Sobrecomisión',
            'percentage': float(commission.percentage_applied),
            'date': commission.date.strftime('%d/%m/%Y'),
            'child_agent': child_agent.name
        }
        
        # Renderizar la plantilla HTML
        msg.html = render_template_string(COMMISSION_EMAIL_TEMPLATE, **template_data)
        
        # Versión texto plano como respaldo
        msg.body = f"""
Estimado/a {agent.name},

Se ha registrado una nueva sobrecomisión a su favor con los siguientes detalles:

Póliza: {policy.policy_number}
Producto: {policy.product.name}
Prima: ${policy.premium:,.2f}
Sobrecomisión: ${commission.amount:,.2f}
Porcentaje aplicado: {commission.percentage_applied}%
Agente: {child_agent.name}
Fecha: {commission.date.strftime('%d/%m/%Y')}

Para ver más detalles, ingrese a su panel de control.

Saludos cordiales,
Sistema de Gestión de Comisiones
"""
        
        mail.send(msg)
        logging.info(f"Notificación de sobrecomisión enviada a {agent.email}")
        return True
        
    except Exception as e:
        logging.error(f"Error al enviar notificación de sobrecomisión: {str(e)}")
        return False

