from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import (
    Policy, 
    Commission, 
    User, 
    Client, 
    Product, 
    db, 
    UserRole, 
    PaymentStatus
)
from sqlalchemy import func, case
from datetime import datetime, timedelta
from decorators import admin_required, admin_or_digitador_required, admin_or_digitador_or_agent_required
from fpdf import FPDF
from flask_mail import Message
from extensions import mail
import os
import logging
import time

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/dashboard')
@login_required
@admin_or_digitador_required
def dashboard():
    # Obtener fechas para filtrado
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Último mes por defecto

    # Estadísticas generales
    total_policies = Policy.query.count()
    total_premium = db.session.query(func.sum(Policy.premium)).scalar() or 0
    total_commissions = db.session.query(func.sum(Commission.amount)).scalar() or 0
    
    # Estadísticas de crecimiento
    previous_month_policies = Policy.query.filter(
        Policy.start_date.between(start_date - timedelta(days=30), start_date)
    ).count()
    current_month_policies = Policy.query.filter(
        Policy.start_date.between(start_date, end_date)
    ).count()
    policy_growth = calculate_growth(previous_month_policies, current_month_policies)

    # Total de clientes activos
    active_clients = Client.query.count()
    previous_clients = Client.query.filter(
        Client.id.in_(
            db.session.query(Policy.client_id).filter(
                Policy.start_date < start_date
            )
        )
    ).count()
    client_growth = calculate_growth(previous_clients, active_clients)

    # Nuevos clientes en el último mes
    new_clients = Client.query.filter(
        Client.id.in_(
            db.session.query(Policy.client_id).filter(
                Policy.start_date.between(start_date, end_date)
            )
        )
    ).count()

    # Datos para gráficos
    weekly_activity = get_weekly_activity()
    daily_sales = get_daily_sales(start_date, end_date)
    completed_policies = get_completed_policies(start_date, end_date)

    # Ventas por país/región
    sales_by_region = get_sales_by_region()

    # Pólizas destacadas
    featured_policies = Policy.query.order_by(Policy.premium.desc()).limit(3).all()

    # Top 5 Clientes por Prima
    top_clients = db.session.query(
        Client.name.label('name'),
        func.sum(Policy.premium).label('total_premium'),
        func.count(Policy.id).label('policy_count')
    ).join(Policy).group_by(Client.id, Client.name)\
    .order_by(func.sum(Policy.premium).desc())\
    .limit(5).all()

    # Top 5 Agentes por Prima
    top_agents = db.session.query(
        User.name.label('name'),
        func.sum(Policy.premium).label('total_premium'),
        func.count(Policy.id).label('policy_count')
    ).join(Policy, User.id == Policy.agent_id)\
    .filter(User.role == UserRole.AGENTE)\
    .group_by(User.id, User.name)\
    .order_by(func.sum(Policy.premium).desc())\
    .limit(5).all()

    # Obtener productos con sus primas del mes actual
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    products_performance = db.session.query(
        Product.name,
        Product.description,
        Product.image_url,
        func.count(Policy.id).label('policy_count'),
        func.sum(Policy.premium).label('total_premium')
    ).outerjoin(
        Policy, 
        db.and_(
            Policy.product_id == Product.id,
            Policy.start_date.between(current_month_start, current_month_end)
        )
    ).group_by(Product.id, Product.name, Product.description, Product.image_url)\
    .order_by(func.sum(Policy.premium).desc())\
    .all()

    return render_template('index.html',
        total_policies=total_policies,
        total_premium=total_premium,
        total_commissions=total_commissions,
        active_clients=active_clients,
        new_clients=new_clients,
        policy_growth=policy_growth,
        client_growth=client_growth,
        weekly_activity=weekly_activity,
        daily_sales=daily_sales,
        completed_policies=completed_policies,
        sales_by_region=sales_by_region,
        featured_policies=featured_policies,
        top_clients=top_clients,
        top_agents=top_agents,
        products_performance=products_performance
    )

def calculate_growth(previous, current):
    if previous == 0:
        return 100 if current > 0 else 0
    return ((current - previous) / previous) * 100

def get_weekly_activity():
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    
    daily_counts = db.session.query(
        func.date_trunc('day', Policy.start_date).label('day'),
        func.count(Policy.id).label('count')
    ).filter(
        Policy.start_date >= week_start
    ).group_by('day').all()
    
    # Crear diccionario con los días de la semana
    week_data = {day: 0 for day in ['L', 'M', 'M', 'J', 'V', 'S', 'D']}
    
    # Llenar con datos reales
    for day_data in daily_counts:
        week_data[day_data.day.strftime('%a')[0]] = day_data.count
    
    return week_data

def get_daily_sales(start_date, end_date):
    daily_sales = db.session.query(
        func.date_trunc('day', Policy.start_date).label('date'),
        func.sum(Policy.premium).label('total')
    ).filter(
        Policy.start_date.between(start_date, end_date)
    ).group_by('date').order_by('date').all()
    
    return {
        'dates': [d.date.strftime('%d/%m') for d in daily_sales],
        'totals': [float(d.total) for d in daily_sales]
    }

def get_completed_policies(start_date, end_date):
    completed = db.session.query(
        func.date_trunc('day', Policy.start_date).label('date'),
        func.count(Policy.id).label('count')
    ).filter(
        Policy.start_date.between(start_date, end_date),
        Policy.emision_status == 'EMITIDA'
    ).group_by('date').order_by('date').all()
    
    return {
        'dates': [d.date.strftime('%d/%m') for d in completed],
        'counts': [d.count for d in completed]
    }

def get_sales_by_region():
    # Corregir las consultas para evitar productos cartesianos
    return [
        {
            'region': 'Costa',
            'sales': Policy.query.join(Client)\
                .filter(Client.city.in_(['Guayaquil', 'Manta']))\
                .count(),
            'value': db.session.query(func.sum(Policy.premium))\
                .join(Client)\
                .filter(Client.city.in_(['Guayaquil', 'Manta']))\
                .scalar() or 0
        },
        {
            'region': 'Sierra',
            'sales': Policy.query.join(Client)\
                .filter(Client.city.in_(['Quito', 'Cuenca']))\
                .count(),
            'value': db.session.query(func.sum(Policy.premium))\
                .join(Client)\
                .filter(Client.city.in_(['Quito', 'Cuenca']))\
                .scalar() or 0
        }
    ]

@bp.route('/sales')
@login_required
@admin_or_digitador_or_agent_required
def sales_report():
    try:
        # Obtener fechas del filtro
        start_date = request.args.get('start_date', 
            default=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', 
            default=datetime.now().strftime('%Y-%m-%d'))

        # Construir la consulta base
        query = db.session.query(
            func.date_trunc('day', Policy.start_date).label('date'),
            func.sum(Policy.premium).label('total_sales'),
            func.count(Policy.id).label('policy_count')
        )

        # Aplicar filtros
        query = query.filter(Policy.start_date.between(start_date, end_date))

        # Si es agente, filtrar solo sus pólizas
        if current_user.role == UserRole.AGENTE:
            query = query.filter(Policy.agent_id == current_user.id)

        # Agrupar y ordenar
        sales = query.group_by(
            func.date_trunc('day', Policy.start_date)
        ).order_by('date').all()

        # Calcular totales
        total_sales = sum(sale.total_sales for sale in sales)
        total_policies = sum(sale.policy_count for sale in sales)

        return render_template(
            'reports/sales.html',
            sales=sales,
            start_date=start_date,
            end_date=end_date,
            total_sales=total_sales,
            total_policies=total_policies
        )
        
    except Exception as e:
        logging.error(f"Error en sales_report: {str(e)}")
        flash('Error al generar el reporte de ventas', 'error')
        return redirect(url_for('reports.dashboard'))

@bp.route('/commissions')
@login_required
def commission_report():
    """Vista para el reporte de comisiones."""
    try:
        # Obtener parámetros de filtro
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        agent_id = request.args.get('agent_id')
        
        # Obtener todos los agentes para el selector
        agents = User.query.filter(
            User.role == UserRole.AGENTE,
            User.name.isnot(None),
            User.name != ''
        ).all()
        
        # Construir la consulta base con la sintaxis correcta de case()
        query = db.session.query(
            User.id.label('agent_id'),
            User.name.label('agent_name'),
            func.coalesce(
                func.sum(
                    case(
                        (Commission.commission_type == 'direct', Commission.amount),
                        else_=0
                    )
                ),
                0
            ).label('direct_commission'),
            func.coalesce(
                func.sum(
                    case(
                        (Commission.commission_type == 'override', Commission.amount),
                        else_=0
                    )
                ),
                0
            ).label('override_commission'),
            func.coalesce(func.sum(Commission.amount), 0).label('total_commission')
        ).filter(
            User.name.isnot(None),
            User.name != ''
        ).outerjoin(
            Commission, User.id == Commission.agent_id
        ).group_by(
            User.id, User.name
        )
        
        # Aplicar filtros
        if start_date:
            query = query.filter(Commission.date >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Commission.date <= datetime.strptime(end_date, '%Y-%m-%d'))
        if agent_id:
            query = query.filter(User.id == agent_id)
        
        # Ejecutar la consulta
        results = query.all()
        
        # Calcular totales
        total_direct_commission = sum(r.direct_commission or 0 for r in results)
        total_override_commission = sum(r.override_commission or 0 for r in results)
        total_commission = total_direct_commission + total_override_commission
        
        return render_template(
            'reports/commissions.html',
            results=results,
            agents=agents,
            start_date=start_date,
            end_date=end_date,
            agent_id=agent_id,
            total_direct_commission=total_direct_commission,
            total_override_commission=total_override_commission,
            total_commission=total_commission
        )
    except Exception as e:
        logging.error(f"Error en commission_report: {str(e)}")
        return render_template('errors/500.html', error=str(e)), 500

@bp.route('/client-analytics')
@login_required
@admin_or_digitador_required
def client_analytics():
    top_clients = db.session.query(
        Client.name, func.count(Policy.id).label('policy_count'), func.sum(Policy.premium).label('total_premium')
    ).join(Policy).group_by(Client.id).order_by(func.sum(Policy.premium).desc()).limit(10).all()
    
    return render_template('reports/client_analytics.html', top_clients=top_clients)

@bp.route('/policy-analytics')
@login_required
@admin_or_digitador_required
def policy_analytics():
    try:
        # Obtener distribución de pólizas por producto
        policy_distribution = db.session.query(
            Product.name.label('name'), 
            func.count(Policy.id).label('policy_count')
        ).outerjoin(
            Policy, 
            Product.id == Policy.product_id
        ).group_by(Product.id, Product.name).all()

        # Obtener tendencia mensual de pólizas (últimos 12 meses)
        twelve_months_ago = datetime.now() - timedelta(days=365)
        policy_trend = db.session.query(
            func.date_trunc('month', Policy.start_date).label('month'),
            func.count(Policy.id).label('policy_count')
        ).filter(
            Policy.start_date >= twelve_months_ago
        ).group_by(
            func.date_trunc('month', Policy.start_date)
        ).order_by('month').all()

        # Obtener prima promedio por producto
        avg_premium_by_product = db.session.query(
            Product.name.label('name'),
            func.round(func.avg(Policy.premium), 2).label('avg_premium')
        ).outerjoin(
            Policy,
            Product.id == Policy.product_id
        ).group_by(Product.id, Product.name).all()

        # Convertir los resultados a diccionarios para facilitar la serialización
        distribution_data = [{'name': d.name, 'policy_count': d.policy_count} for d in policy_distribution]
        trend_data = [{'month': t.month.strftime('%Y-%m'), 'policy_count': t.policy_count} for t in policy_trend]
        premium_data = [{'name': p.name, 'avg_premium': float(p.avg_premium or 0)} for p in avg_premium_by_product]

        return render_template(
            'reports/policy_analytics.html',
            policy_distribution=distribution_data,
            policy_trend=trend_data,
            avg_premium_by_product=premium_data
        )
        
    except Exception as e:
        logging.error(f"Error en policy_analytics: {str(e)}")
        flash('Error al generar el reporte de análisis de pólizas', 'error')
        return redirect(url_for('reports.dashboard'))

@bp.route('/diagram')
@login_required
@admin_required
def diagram():
    try:
        # Verificar que tenemos acceso a la base de datos
        agents = User.query.filter_by(role=UserRole.AGENTE).all()
        if not agents:
            # Si no hay agentes, devolver una estructura básica
            return render_template('reports/diagram.html', error_message="No hay agentes para mostrar")
            
        return render_template('reports/diagram.html')
    except Exception as e:
        # Registrar el error
        logging.error(f"Error en la ruta /diagram: {str(e)}")
        # Devolver una respuesta más amigable
        return render_template('errors/500.html'), 500

@bp.route('/api/agent-hierarchy')
@login_required
@admin_required
def agent_hierarchy_data():
    try:
        def get_agent_hierarchy(agent):
            return {
                "id": agent.id,
                "name": agent.username,
                "role": agent.role.value,
                "children": [get_agent_hierarchy(subordinate) for subordinate in agent.subordinates]
            }

        # Obtener solo los agentes raíz (sin supervisor)
        root_agents = User.query.filter_by(
            role=UserRole.AGENTE,
            parent_id=None
        ).all()

        if not root_agents:
            return jsonify({
                "name": "Agentes",
                "children": []
            })

        hierarchy = {
            "name": "Agentes",
            "children": [get_agent_hierarchy(agent) for agent in root_agents]
        }

        return jsonify(hierarchy)
    except Exception as e:
        logging.error(f"Error al generar jerarquía de agentes: {str(e)}")
        return jsonify({"error": "Error al generar el diagrama"}), 500

@bp.route('/agent-commission-details/<int:agent_id>')
@login_required
def agent_commission_details(agent_id):
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Asegurarse de que agent_id sea un entero
        agent_id = int(agent_id)
        agent = User.query.get_or_404(agent_id)
        
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
        
        commissions = query.all()
        
        total_pending = sum(float(c.Commission.amount) for c in commissions if c.Commission.payment_status == 'PENDIENTE')
        total_paid = sum(float(c.Commission.amount) for c in commissions if c.Commission.payment_status == 'PAGADO')
        total_commission = total_pending + total_paid
        
        return render_template(
            'reports/agent_commission_details.html',
            agent=agent,
            commissions=commissions,
            start_date=start_date,
            end_date=end_date,
            total_pending=total_pending,
            total_paid=total_paid,
            total_commission=total_commission
        )
    except ValueError as e:
        logging.error(f"Error de conversión de ID: {str(e)}")
        return render_template('errors/500.html', error="ID de agente inválido"), 500
    except Exception as e:
        logging.error(f"Error en agent_commission_details: {str(e)}")
        return render_template('errors/500.html', error=str(e)), 500

@bp.route('/generate_commission_report/<int:agent_id>', methods=['POST'])
@login_required
def generate_commission_report(agent_id):
    """Genera un reporte de comisiones para un agente específico y lo envía por correo."""
    # Obtener el agente
    agent = User.query.get_or_404(agent_id)
    
    # Obtener las comisiones pendientes usando el valor del enum
    commissions = Commission.query.filter_by(
        agent_id=agent_id, 
        payment_status='PENDIENTE'  # Usar string en lugar del enum
    ).all()
    
    if not commissions:
        flash('No hay comisiones pendientes para este agente.', 'info')
        return redirect(url_for('reports.commission_report'))

    try:
        # Asegurarse de que existe el directorio reports
        os.makedirs('reports', exist_ok=True)
        
        # Crear el PDF
        pdf = create_commission_pdf(agent, commissions)

        # Enviar el PDF por correo
        send_commission_report_email(agent.email, pdf)

        # Marcar las comisiones como pagadas
        for commission in commissions:
            commission.payment_status = 'PAGADO'  # Usar string en lugar del enum

        db.session.commit()
        flash('El reporte de comisiones ha sido enviado exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error al generar reporte: {str(e)}")
        flash(f'Error al generar el reporte: {str(e)}', 'error')
    
    return redirect(url_for('reports.commission_report'))

def create_commission_pdf(agent, commissions):
    """Crea un PDF con el reporte de comisiones con diseño profesional."""
    try:
        pdf_filename = f"commission_report_{agent.id}_{int(time.time())}.pdf"
        pdf_path = os.path.join('reports', pdf_filename)
        
        class PDF(FPDF):
            def header(self):
                # Logo de Previanza
                logo_path = os.path.join('static', 'img', 'logo.png')  # Asegúrate de que el logo esté en esta ruta
                if os.path.exists(logo_path):
                    self.image(logo_path, x=10, y=8, w=60)  # Ajusta el tamaño según necesites
                
                # Línea decorativa superior
                self.set_draw_color(0, 84, 159)  # Color azul de Previanza
                self.set_line_width(0.5)
                self.line(10, 30, 200, 30)
                
                # Título del reporte
                self.ln(25)  # Espacio después del logo
                self.set_font('Arial', 'B', 20)
                self.set_text_color(0, 84, 159)  # Color azul de Previanza
                self.cell(0, 20, 'Reporte de Comisiones', 0, 1, 'C')
                
                # Información del agente
                self.set_font('Arial', 'B', 12)
                self.set_text_color(70, 70, 70)
                self.cell(0, 8, f'Agente: {agent.name}', 0, 1, 'C')
                self.set_font('Arial', '', 10)
                self.cell(0, 6, f'Fecha de Emisión: {datetime.now().strftime("%d/%m/%Y")}', 0, 1, 'C')
                
                # Línea decorativa inferior
                self.set_draw_color(0, 84, 159)
                self.line(10, self.get_y() + 5, 200, self.get_y() + 5)
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.set_text_color(128)
                self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')
                
                # Línea decorativa en el pie de página
                self.set_draw_color(0, 84, 159)
                self.line(10, self.get_y() - 3, 200, self.get_y() - 3)

        # Crear PDF
        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Información del período
        pdf.set_font('Arial', 'B', 11)
        pdf.set_text_color(70, 70, 70)
        pdf.cell(0, 10, 'Resumen de Comisiones Pendientes', 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        pdf.ln(5)

        # Crear tabla de comisiones
        # Encabezados
        pdf.set_fill_color(0, 84, 159)  # Color azul de Previanza
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 10)
        
        # Ancho de columnas
        col_widths = [25, 35, 45, 30, 30, 25]
        headers = ['Fecha', 'Póliza', 'Producto', 'Prima', 'Comisión', 'Tipo']
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1, 0, 'C', True)
        pdf.ln()

        # Contenido de la tabla
        pdf.set_text_color(70, 70, 70)
        pdf.set_font('Arial', '', 9)
        total_commission = 0
        fill = False

        for commission in commissions:
            policy = Policy.query.get(commission.policy_id)
            product = Product.query.get(policy.product_id)
            
            # Alternar colores de fondo
            if fill:
                pdf.set_fill_color(240, 240, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
                
            pdf.cell(col_widths[0], 8, commission.date.strftime('%d/%m/%Y'), 1, 0, 'C', fill)
            pdf.cell(col_widths[1], 8, policy.policy_number, 1, 0, 'C', fill)
            pdf.cell(col_widths[2], 8, product.name, 1, 0, 'L', fill)
            pdf.cell(col_widths[3], 8, f"${float(policy.premium):,.2f}", 1, 0, 'R', fill)
            pdf.cell(col_widths[4], 8, f"${float(commission.amount):,.2f}", 1, 0, 'R', fill)
            pdf.cell(col_widths[5], 8, 'Directa' if commission.commission_type == 'direct' else 'Override', 1, 0, 'C', fill)
            pdf.ln()
            
            total_commission += float(commission.amount)
            fill = not fill

        # Total
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 84, 159)
        pdf.cell(sum(col_widths[:4]), 10, 'Total:', 1, 0, 'R')
        pdf.cell(col_widths[4], 10, f"${total_commission:,.2f}", 1, 0, 'R')
        pdf.cell(col_widths[5], 10, '', 1, 1, 'C')

        # Agregar información adicional
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 10, 'Información Adicional', 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, (
            'Este reporte incluye todas las comisiones pendientes de pago hasta la fecha. '
            'Las comisiones serán procesadas para pago una vez este reporte sea generado.'
        ))

        # Agregar firmas
        pdf.ln(20)
        pdf.set_font('Arial', '', 10)
        pdf.cell(90, 10, '_' * 30, 0, 0, 'C')
        pdf.cell(90, 10, '_' * 30, 0, 1, 'C')
        pdf.cell(90, 5, 'Firma del Agente', 0, 0, 'C')
        pdf.cell(90, 5, 'Autorizado por', 0, 1, 'C')

        pdf.output(pdf_path)
        return pdf_path

    except Exception as e:
        logging.error(f"Error creando PDF: {str(e)}")
        raise

def send_commission_report_email(recipient_email, pdf_file_path):
    """Envía el reporte de comisiones por correo electrónico."""
    try:
        msg = Message(
            "Reporte de Comisiones",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[recipient_email]
        )
        msg.body = """
        Estimado agente,

        Adjunto encontrará su reporte de comisiones.

        Saludos cordiales,
        """

        with open(pdf_file_path, 'rb') as f:
            msg.attach(
                "reporte_comisiones.pdf",
                "application/pdf",
                f.read()
            )

        mail.send(msg)
        return True

    except Exception as e:
        logging.error(f"Error enviando email: {str(e)}")
        raise

@bp.route('/update_commission_status/<int:commission_id>', methods=['POST'])
@login_required
@admin_required
def update_commission_status(commission_id):
    """Actualiza el estado de una comisión."""
    commission = Commission.query.get_or_404(commission_id)
    new_status = request.form.get('status')
    
    if new_status not in ['PENDIENTE', 'PAGADO', 'ANULADO']:
        return jsonify({'success': False, 'message': 'Estado inválido'}), 400
        
    try:
        commission.payment_status = new_status
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Estado actualizado a {new_status}',
            'new_status': new_status
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/mass-commission-report')
@login_required
@admin_required
def mass_commission_report():
    """Vista para el reporte de comisiones masivo."""
    try:
        # Obtener agentes con comisiones pendientes
        agent_data = []
        agents_query = db.session.query(
            User,
            func.count(Commission.id).label('pending_count'),
            func.sum(Commission.amount).label('pending_amount')
        ).join(
            Commission, User.id == Commission.agent_id
        ).filter(
            User.role == UserRole.AGENTE,
            Commission.payment_status == 'PENDIENTE'
        ).group_by(User.id).all()

        for agent, pending_count, pending_amount in agents_query:
            agent_data.append({
                'agent': agent,
                'pending_count': pending_count,
                'pending_amount': pending_amount or 0
            })

        # Calcular totales
        total_pending_count = sum(data['pending_count'] for data in agent_data)
        total_pending_amount = sum(data['pending_amount'] for data in agent_data)

        return render_template(
            'reports/mass_commission_report.html',
            agent_data=agent_data,
            total_pending_count=total_pending_count,
            total_pending_amount=total_pending_amount
        )
    except Exception as e:
        logging.error(f"Error en mass_commission_report: {str(e)}")
        return render_template('errors/500.html', error=str(e)), 500

@bp.route('/confirm-mass-commission-report', methods=['POST'])
@login_required
@admin_required
def confirm_mass_commission_report():
    """Confirmar el pago masivo de comisiones."""
    try:
        agent_ids = request.form.getlist('agent_ids')
        if not agent_ids:
            flash('Debe seleccionar al menos un agente.', 'warning')
            return redirect(url_for('reports.mass_commission_report'))

        agents = User.query.filter(User.id.in_(agent_ids)).all()
        agent_commissions = {}

        for agent in agents:
            commissions = Commission.query.filter_by(
                agent_id=agent.id,
                payment_status='PENDIENTE'
            ).all()
            
            agent_commissions[agent.id] = {
                'count': len(commissions),
                'total': sum(float(c.amount) for c in commissions)
            }

        return render_template(
            'reports/confirm_mass_commission_report.html',
            agents=agents,
            agent_commissions=agent_commissions
        )
    except Exception as e:
        logging.error(f"Error en confirm_mass_commission_report: {str(e)}")
        return render_template('errors/500.html', error=str(e)), 500

@bp.route('/process-mass-commission-report', methods=['POST'])
@login_required
@admin_required
def process_mass_commission_report():
    """Procesar el pago masivo de comisiones."""
    try:
        results = {
            'success': [],
            'errors': [],
            'no_commissions': []
        }

        agent_ids = request.form.getlist('agent_ids')
        if not agent_ids:
            flash('Debe seleccionar al menos un agente.', 'warning')
            return redirect(url_for('reports.mass_commission_report'))

        for agent_id in agent_ids:
            try:
                agent = User.query.get(agent_id)
                if not agent:
                    continue

                # Obtener comisiones pendientes
                commissions = Commission.query.filter_by(
                    agent_id=agent_id,
                    payment_status='PENDIENTE'
                ).all()

                if not commissions:
                    results['no_commissions'].append(agent.name)
                    continue

                # Crear directorio para reportes si no existe
                os.makedirs('reports', exist_ok=True)

                # Crear y enviar el reporte
                try:
                    pdf_path = create_commission_pdf(agent, commissions)
                    if pdf_path and os.path.exists(pdf_path):
                        send_commission_report_email(agent.email, pdf_path)
                        
                        # Actualizar estado de comisiones solo si el envío fue exitoso
                        for commission in commissions:
                            commission.payment_status = 'PAGADO'
                        
                        db.session.commit()
                        results['success'].append(agent.name)
                        
                        # Limpiar el archivo PDF después de enviarlo
                        try:
                            os.remove(pdf_path)
                        except:
                            pass
                    else:
                        raise Exception("Error al generar el PDF")
                        
                except Exception as e:
                    db.session.rollback()
                    results['errors'].append({
                        'agent_name': agent.name,
                        'reason': f"Error al procesar el reporte: {str(e)}"
                    })
                    logging.error(f"Error procesando comisiones para {agent.name}: {str(e)}")
                    continue

            except Exception as e:
                results['errors'].append({
                    'agent_name': agent.name if agent else f"ID: {agent_id}",
                    'reason': str(e)
                })
                logging.error(f"Error procesando agente {agent_id}: {str(e)}")
                continue

        return render_template('reports/mass_commission_results.html', results=results)

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error en process_mass_commission_report: {str(e)}")
        return render_template('errors/500.html', error=str(e)), 500

@bp.route('/update_multiple_commission_status', methods=['POST'])
@login_required
@admin_required
def update_multiple_commission_status():
    """Actualiza el estado de múltiples comisiones."""
    try:
        agent_id = request.form.get('agent_id')
        
        # Procesar cada comisión
        for key, new_status in request.form.items():
            if key.startswith('status_') and new_status:
                try:
                    commission_id = int(key.replace('status_', ''))
                    commission = Commission.query.get(commission_id)
                    
                    if commission and new_status in ['PENDIENTE', 'PAGADO', 'ANULADO']:
                        commission.payment_status = new_status
                except ValueError:
                    continue
        
        db.session.commit()
        flash('Estados actualizados exitosamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar los estados: {str(e)}', 'error')
        logging.error(f"Error actualizando estados de comisiones: {str(e)}")
    
    return redirect(url_for('reports.agent_commission_details', agent_id=agent_id))
