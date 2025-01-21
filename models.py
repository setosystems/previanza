from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Date, ForeignKey, Enum, Numeric, DateTime, Boolean
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import enum
from datetime import datetime, timedelta, timezone  # Agregar timezone a los imports
import secrets
from utils.email import send_commission_notification, send_override_commission_notification, queue_commission_notification, queue_override_commission_notification
from decimal import Decimal
import logging

db = SQLAlchemy()

class UserRole(enum.Enum):
    """
    Enumeración para los roles de usuario.
    """
    ADMIN = "Administrador"
    DIGITADOR = "Digitador"
    AGENTE = "Agente de Ventas"

class DocumentType(enum.Enum):
    """
    Enumeración para los tipos de documentos.
    """
    DNI = "Cédula"
    PASAPORTE = "Pasaporte"
    CARNET_EXTRANJERIA = "Cédula de Extranjería"

class User(UserMixin, db.Model):
    """
    Modelo para los usuarios.
    """
    id = db.Column(Integer, primary_key=True)
    username = db.Column(String(255), unique=True, nullable=False)
    email = db.Column(String(255), unique=True, nullable=False)
    password_hash = db.Column(String(512))
    role = db.Column(Enum(UserRole), nullable=False)
    name = db.Column(String(255))
    phone = db.Column(String(20))
    address = db.Column(String(255))
    date_of_birth = db.Column(Date)
    hire_date = db.Column(Date)
    document_type = db.Column(Enum(DocumentType), nullable=False)
    document_number = db.Column(String(20), nullable=False)
    parent_id = db.Column(Integer, ForeignKey('user.id'))
    parent = relationship("User", remote_side=[id], back_populates="subordinates")
    subordinates = relationship("User", back_populates="parent")
    reset_password_token = db.Column(String(100), unique=True)
    reset_password_expiration = db.Column(db.DateTime(timezone=True))

    # Añadir relaciones bidireccionales con Policy y Commission
    policies = relationship('Policy', back_populates='agent', cascade='all, delete-orphan')
    commissions = relationship('Commission', back_populates='agent', cascade='all, delete-orphan')

    commission_overrides = relationship('AgentCommissionOverride', back_populates='agent')

    __table_args__ = (
        db.UniqueConstraint('document_type', 'document_number', name='uq_user_document'),
    )

    def __init__(self, username, email, role, document_type, document_number, name=None, phone=None, address=None, date_of_birth=None, hire_date=None, parent_id=None):
        self.username = username
        self.email = email
        self.role = role
        self.document_type = document_type  # Agregado
        self.document_number = document_number  # Agregado
        self.name = name
        self.phone = phone
        self.address = address
        self.date_of_birth = date_of_birth
        self.hire_date = hire_date
        self.parent_id = parent_id

    def set_password(self, password):
        """
        Genera un hash de la contraseña y lo almacena.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifica la contraseña contra el hash almacenado.
        """
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        """
        Verifica si el usuario tiene el rol especificado.
        """
        return self.role == role

    def generate_reset_token(self):
        """
        Genera un token de restablecimiento de contraseña y establece su tiempo de expiración.
        """
        self.reset_password_token = secrets.token_urlsafe(32)
        # Asegurarnos de usar UTC consistentemente
        self.reset_password_expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()
        return self.reset_password_token

    def verify_reset_token(self, token):
        """
        Verifica si el token de restablecimiento de contraseña es válido y no ha expirado.
        """
        if token != self.reset_password_token:
            return False
        
        if self.reset_password_expiration is None:
            return False
            
        # Asegurarnos de que la fecha actual tenga timezone
        now = datetime.now(timezone.utc)
        
        # Asegurarnos de que reset_password_expiration tenga timezone si no lo tiene
        expiration = self.reset_password_expiration
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=timezone.utc)
            
        return now <= expiration

    def get_commission_percentage(self, product):
        """
        Obtiene el porcentaje de comisión para un producto específico.
        """
        override = AgentCommissionOverride.query.filter_by(
            agent_id=self.id,
            product_id=product.id
        ).first()
        
        if override:
            return override.commission_percentage
        return product.commission_percentage

    def calculate_commission(self, policy):
        """
        Calcula y registra la comisión para una póliza.
        La comisión directa va al agente que vendió.
        La sobrecomisión se distribuye equitativamente entre todos los supervisores.
        """
        if policy.payment_status != PaymentStatus.PAGADO:
            return None

        try:
            # Obtener la prima en formato Decimal
            premium_decimal = Decimal(str(float(policy.premium)))
            
            # Obtener el porcentaje de comisión del producto
            commission_percentage = self.get_commission_percentage(policy.product)
            
            # Calcular la comisión total
            total_commission = (premium_decimal * commission_percentage) / Decimal('100')
            
            logging.info(f"Calculando comisión para póliza {policy.policy_number}")
            logging.info(f"Prima: {premium_decimal}")
            logging.info(f"Porcentaje de comisión total: {commission_percentage}%")
            
            # Si el producto tiene sobrecomisión y el agente tiene supervisores
            if policy.product.sobrecomision and self.parent_id:
                # Obtener toda la cadena de supervisores
                supervisors = []
                current_agent = self
                while current_agent.parent_id:
                    supervisors.append(current_agent.parent)
                    current_agent = current_agent.parent
                
                # Obtener el porcentaje de sobrecomisión del producto
                override_percentage = Decimal(str(float(policy.product.override_percentage)))
                
                # Calcular el monto total de sobrecomisión
                total_override = (premium_decimal * override_percentage) / Decimal('100')
                
                # Calcular la parte de sobrecomisión para cada supervisor
                if supervisors:
                    override_per_supervisor = total_override / Decimal(str(len(supervisors)))
                else:
                    override_per_supervisor = Decimal('0')
                
                # La comisión del agente es la comisión total menos la sobrecomisión total
                agent_amount = total_commission - total_override
                
                logging.info(f"Sobrecomisión total: {total_override}")
                logging.info(f"Número de supervisores: {len(supervisors)}")
                logging.info(f"Sobrecomisión por supervisor: {override_per_supervisor}")
                logging.info(f"Comisión del agente: {agent_amount}")
            else:
                # Si no hay supervisores o no hay sobrecomisión, toda la comisión va al agente
                agent_amount = total_commission
                override_per_supervisor = Decimal('0')
                supervisors = []
                
            # Crear la comisión principal para el agente vendedor
            main_commission = Commission(
                amount=agent_amount,
                date=datetime.now(timezone.utc).date(),
                policy_id=policy.id,
                agent_id=self.id,
                commission_type='direct',
                percentage_applied=commission_percentage
            )
            db.session.add(main_commission)
            db.session.flush()
            
            # Encolar notificación al agente
            queue_commission_notification(self, main_commission, policy)

            # Crear las comisiones para cada supervisor
            if supervisors and override_per_supervisor > 0:
                for supervisor in supervisors:
                    override_commission = Commission(
                        amount=override_per_supervisor,
                        date=datetime.now(timezone.utc).date(),
                        policy_id=policy.id,
                        agent_id=supervisor.id,
                        commission_type='override',
                        percentage_applied=override_percentage / Decimal(str(len(supervisors))),
                        parent_commission_id=main_commission.id
                    )
                    db.session.add(override_commission)
                    
                    # Encolar notificación al supervisor
                    queue_override_commission_notification(
                        supervisor,
                        override_commission,
                        policy,
                        self
                    )
            
            return main_commission
            
        except Exception as e:
            logging.error(f"Error en calculate_commission: {str(e)}")
            db.session.rollback()
            raise

    def get_total_commissions(self, start_date=None, end_date=None):
        """
        Obtiene el total de comisiones para un agente en un período específico.
        """
        query = Commission.query.filter_by(agent_id=self.id)
        
        if start_date:
            query = query.filter(Commission.date >= start_date)
        if end_date:
            query = query.filter(Commission.date <= end_date)
            
        return query.with_entities(db.func.sum(Commission.amount)).scalar() or 0

    def get_commission_details(self, start_date=None, end_date=None):
        """
        Obtiene los detalles de las comisiones para un agente.
        """
        query = db.session.query(
            Commission,
            Policy,
            Product
        ).join(
            Policy, Commission.policy_id == Policy.id
        ).join(
            Product, Policy.product_id == Product.id
        ).filter(
            Commission.agent_id == self.id
        )

        if start_date:
            query = query.filter(Commission.date >= start_date)
        if end_date:
            query = query.filter(Commission.date <= end_date)

        return query.all()

class Client(db.Model):
    """
    Modelo para los clientes.
    """
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    phone = db.Column(String(20))
    address = db.Column(String(200))
    city = db.Column(String(100))
    document_type = db.Column(Enum(DocumentType))
    document_number = db.Column(String(20))
    birthdate = db.Column(Date)
    policies = relationship('Policy', back_populates='client')

    __table_args__ = (
        db.UniqueConstraint('document_type', 'document_number', name='uq_client_document'),
    )

class Product(db.Model):
    """
    Modelo para los productos.
    """
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    description = db.Column(db.String(2000))
    aseguradora = db.Column(String(100))
    sobrecomision = db.Column(Boolean, default=False)
    commission_percentage = db.Column(Numeric(5, 2), nullable=False, default=0)
    override_percentage = db.Column(Numeric(5, 2), nullable=False, default=0)
    image_url = db.Column(String(255))  # Nuevo campo para la imagen
    policies = relationship('Policy', back_populates='product')

class EmisionStatus(enum.Enum):
    PENDIENTE = "Pendiente"
    EMITIDA = "Emitida"
    CADUCADA = "Caducada"
    ANULADA = "Anulada"
    OTROS = "Otros"

class PaymentStatus(enum.Enum):
    PENDIENTE = "Pendiente"
    PAGADO = "Pagado"
    ABONADO = "Abonado"
    REEMBOLSADO = "Reembolsado"
    OTROS = "Otros"

class Policy(db.Model):
    """
    Modelo para las pólizas.
    """
    id = db.Column(Integer, primary_key=True)
    policy_number = db.Column(String(50), unique=True, nullable=False)
    start_date = db.Column(Date, nullable=False)
    end_date = db.Column(Date, nullable=False)
    premium = db.Column(Numeric(10, 2), nullable=False)
    client_id = db.Column(Integer, ForeignKey('client.id'), nullable=False)
    product_id = db.Column(Integer, ForeignKey('product.id'), nullable=False)
    agent_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    emision_status = db.Column(Enum(EmisionStatus), nullable=False, default=EmisionStatus.PENDIENTE)
    payment_status = db.Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDIENTE)
    client = relationship('Client', back_populates='policies')
    product = relationship('Product', back_populates='policies')
    agent = relationship('User', back_populates='policies')
    commissions = relationship('Commission', back_populates='policy', cascade='all, delete-orphan')

class Commission(db.Model):
    """
    Modelo para las comisiones.
    """
    id = db.Column(Integer, primary_key=True)
    amount = db.Column(Numeric(10, 2), nullable=False)
    date = db.Column(Date, nullable=False)
    policy_id = db.Column(Integer, ForeignKey('policy.id'), nullable=False)
    agent_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    commission_type = db.Column(String(20), nullable=False, default='direct')
    percentage_applied = db.Column(Numeric(5, 2), nullable=False)
    parent_commission_id = db.Column(Integer, ForeignKey('commission.id'))
    payment_status = db.Column(String(50), nullable=False, default='PENDIENTE')
    
    policy = relationship('Policy', back_populates='commissions')
    agent = relationship('User', back_populates='commissions')
    parent_commission = relationship('Commission', remote_side=[id], backref='child_commissions')

class AgentCommissionOverride(db.Model):
    """
    Modelo para comisiones personalizadas por agente y producto.
    """
    id = db.Column(Integer, primary_key=True)
    agent_id = db.Column(Integer, ForeignKey('user.id'), nullable=False)
    product_id = db.Column(Integer, ForeignKey('product.id'), nullable=False)
    commission_percentage = db.Column(Numeric(5, 2), nullable=False)
    override_percentage = db.Column(Numeric(5, 2), nullable=False, default=0)  # Nuevo campo
    
    agent = relationship('User', back_populates='commission_overrides')
    product = relationship('Product')

    __table_args__ = (db.UniqueConstraint('agent_id', 'product_id'),)

class SMTPConfig(db.Model):
    """
    Modelo para la configuración SMTP.
    """
    id = db.Column(Integer, primary_key=True)
    mail_server = db.Column(String(255), nullable=False)
    mail_port = db.Column(Integer, nullable=False)
    mail_use_tls = db.Column(Boolean, default=False)
    mail_use_ssl = db.Column(Boolean, default=True)
    mail_username = db.Column(String(255), nullable=False)
    mail_password = db.Column(String(255), nullable=False)
    mail_default_sender = db.Column(String(255), nullable=False)
    is_active = db.Column(Boolean, default=False)
    last_updated = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @classmethod
    def get_active_config(cls):
        """
        Obtiene la configuración SMTP activa.
        """
        return cls.query.filter_by(is_active=True).first()

    @classmethod
    def deactivate_all(cls):
        """
        Desactiva todas las configuraciones SMTP existentes.
        """
        cls.query.update({cls.is_active: False})
        db.session.commit()

try:
    from utils.email import send_commission_notification, send_override_commission_notification
except ImportError:
    # Funciones temporales en caso de que el módulo no esté disponible
    def send_commission_notification(agent, commission, policy):
        print(f"Mock: Enviando notificación de comisión a {agent.email}")
        return True
        
    def send_override_commission_notification(agent, commission, policy, child_agent):
        print(f"Mock: Enviando notificación de sobrecomisión a {agent.email}")
        return True
