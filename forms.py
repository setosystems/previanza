from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, DateField, HiddenField, IntegerField, BooleanField, DecimalField, EmailField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, Length, NumberRange
from models import User, UserRole, DocumentType, EmisionStatus, PaymentStatus, Client, Policy
import logging

def validate_ecuador_id(cedula):
    """
    Valida una cédula ecuatoriana usando el algoritmo oficial.
    Retorna True si es válida, False si no lo es.
    """
    if len(cedula) != 10 or not cedula.isdigit():
        return False

    # Verificar los dos primeros dígitos (provincia)
    provincia = int(cedula[:2])
    if provincia < 1 or provincia > 24:
        return False

    # Obtener el último dígito (verificador)
    verificador = int(cedula[-1])

    # Calcular el dígito verificador
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    for i in range(9):
        valor = int(cedula[i]) * coeficientes[i]
        suma += valor if valor < 10 else valor - 9

    resultado = 10 - (suma % 10)
    if resultado == 10:
        resultado = 0

    return resultado == verificador

class LoginForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Rol', choices=[(role.name, role.value) for role in UserRole])
    name = StringField('Nombre Completo')
    phone = StringField('Teléfono')
    address = StringField('Dirección')
    date_of_birth = DateField('Fecha de Nacimiento', format='%Y-%m-%d', validators=[Optional()])
    hire_date = DateField('Fecha de Contratación', format='%Y-%m-%d', validators=[Optional()])
    parent_id = SelectField('Superior', coerce=int, validators=[Optional()])
    
    # Campos agregados
    document_type = SelectField('Tipo de Documento', choices=[(dt.name, dt.value) for dt in DocumentType], validators=[DataRequired()])
    document_number = StringField('Número de Documento', validators=[DataRequired()])

    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Por favor, use un nombre de usuario diferente.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Por favor, use una dirección de correo electrónico diferente.')

class UserEditForm(FlaskForm):
    id = HiddenField('ID')  # Campo oculto para guardar el ID del usuario
    username = StringField('Nombre de Usuario', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    role = SelectField('Rol', choices=[(role.name, role.value) for role in UserRole])
    name = StringField('Nombre Completo')
    phone = StringField('Teléfono')
    address = StringField('Dirección')
    date_of_birth = DateField('Fecha de Nacimiento', format='%Y-%m-%d', validators=[Optional()])
    hire_date = DateField('Fecha de Contratación', format='%Y-%m-%d', validators=[Optional()])
    parent_id = SelectField('Superior', coerce=int, validators=[Optional()])
    
    # Campos agregados
    document_type = SelectField('Tipo de Documento', choices=[(dt.name, dt.value) for dt in DocumentType], validators=[DataRequired()])
    document_number = StringField('Número de Documento', validators=[DataRequired()])

    submit = SubmitField('Guardar Cambios')

    def validate_username(self, username):
        if self.id.data:
            user = User.query.filter(
                User.username == username.data,
                User.id != int(self.id.data)
            ).first()
            if user is not None:
                raise ValidationError('Por favor, use un nombre de usuario diferente.')
        else:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Por favor, use un nombre de usuario diferente.')

    def validate_email(self, email):
        if self.id.data:
            user = User.query.filter(
                User.email == email.data,
                User.id != int(self.id.data)
            ).first()
            if user is not None:
                raise ValidationError('Por favor, use una dirección de correo electrónico diferente.')
        else:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Por favor, use una dirección de correo electrónico diferente.')
                
    def validate_document_number(self, field):
        """
        Valida que la combinación tipo de documento y número de documento sea única.
        """
        try:
            document_type_enum = DocumentType[self.document_type.data] if self.document_type.data else None
            
            # Si no hay tipo de documento o número, no validamos unicidad
            if not document_type_enum or not field.data:
                return
                
            # Verificar si es una edición (id existe) o creación nueva
            if self.id.data:
                # Es una edición - excluir el usuario actual de la validación
                user = User.query.filter(
                    User.document_type == document_type_enum,
                    User.document_number == field.data,
                    User.id != int(self.id.data)
                ).first()
                
                if user is not None:
                    raise ValidationError(f'Ya existe un usuario con el documento {document_type_enum.value}: {field.data}')
            else:
                # Es una creación nueva - verificar si la combinación documento+tipo existe
                user = User.query.filter_by(
                    document_type=document_type_enum,
                    document_number=field.data
                ).first()
                
                if user is not None:
                    raise ValidationError(f'Ya existe un usuario con el documento {document_type_enum.value}: {field.data}')
        except Exception as e:
            # En caso de error en la validación, registramos el error pero no bloqueamos
            logging.error(f"Error en validación de documento de usuario: {str(e)}")

class RequestResetForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar Restablecimiento de Contraseña')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('No existe una cuenta con ese correo electrónico.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[DataRequired()])
    password2 = PasswordField('Confirmar Nueva Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Restablecer Contraseña')

class ClientForm(FlaskForm):
    id = HiddenField('ID')  # Campo oculto para guardar el ID del cliente
    name = StringField('Nombre', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    phone = StringField('Teléfono', validators=[DataRequired()])
    address = StringField('Dirección')
    city = StringField('Ciudad')
    document_type = SelectField('Tipo de Documento', choices=[(dt.name, dt.value) for dt in DocumentType])
    document_number = StringField('Número de Documento', validators=[DataRequired()])
    birthdate = DateField('Fecha de Nacimiento', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Guardar')

    def validate_email(self, email):
        # Verificar si es una edición (id existe) o creación nueva
        if self.id.data:
            # Es una edición - excluir el cliente actual de la validación
            client = Client.query.filter_by(email=email.data).first()
            if client is not None and str(client.id) != self.id.data:
                raise ValidationError('Este correo electrónico ya está registrado. Por favor use uno diferente.')
        else:
            # Es una creación nueva - verificar si el email existe
            client = Client.query.filter_by(email=email.data).first()
            if client is not None:
                raise ValidationError('Este correo electrónico ya está registrado. Por favor use uno diferente.')

    def validate_document_number(self, field):
        """
        Valida el número de documento según el tipo seleccionado y verifica unicidad.
        """
        # Primero validamos el formato según el tipo de documento
        if self.document_type.data == 'DNI':  # Si es cédula ecuatoriana
            if not validate_ecuador_id(field.data):
                raise ValidationError('El número de cédula ingresado no es válido. Verifique que sea una cédula ecuatoriana válida.')
        elif self.document_type.data == 'PASAPORTE':
            if len(field.data) < 6:
                raise ValidationError('El número de pasaporte debe tener al menos 6 caracteres.')
        elif self.document_type.data == 'CARNET_EXTRANJERIA':
            if not field.data.isalnum() or len(field.data) < 4:
                raise ValidationError('El número de carnet de extranjería no es válido.')
        
        # Ahora verificamos la unicidad, excluyendo el cliente actual si es una edición
        try:
            document_type_enum = DocumentType[self.document_type.data] if self.document_type.data else None
            
            # Si no hay tipo de documento o número, no validamos unicidad
            if not document_type_enum or not field.data:
                return
                
            # Verificar si es una edición (id existe) o creación nueva
            if self.id.data:
                # Es una edición - excluir el cliente actual de la validación
                client = Client.query.filter(
                    Client.document_type == document_type_enum,
                    Client.document_number == field.data,
                    Client.id != int(self.id.data)
                ).first()
                
                if client is not None:
                    raise ValidationError(f'Ya existe un cliente con el documento {document_type_enum.value}: {field.data}')
            else:
                # Es una creación nueva - verificar si la combinación documento+tipo existe
                client = Client.query.filter_by(
                    document_type=document_type_enum,
                    document_number=field.data
                ).first()
                
                if client is not None:
                    raise ValidationError(f'Ya existe un cliente con el documento {document_type_enum.value}: {field.data}')
        except Exception as e:
            # En caso de error en la validación, registramos el error pero no bloqueamos
            logging.error(f"Error en validación de documento: {str(e)}")

class PolicyForm(FlaskForm):
    id = HiddenField('ID')  # Campo oculto para guardar el ID de la póliza
    policy_number = StringField('Número de Póliza', validators=[DataRequired()])
    start_date = DateField('Fecha de Inicio', validators=[DataRequired()])
    end_date = DateField('Fecha de Fin', validators=[DataRequired()])
    premium = FloatField('Prima', validators=[DataRequired()])
    client = StringField('Cliente', validators=[DataRequired()])
    client_id = HiddenField('ID del Cliente')
    product_id = SelectField('Producto', coerce=int, validators=[DataRequired()])
    agent = StringField('Agente', validators=[DataRequired()])
    agent_id = HiddenField('ID del Agente')
    emision_status = SelectField('Estado de Emisión', choices=[(status.name, status.value) for status in EmisionStatus], validators=[DataRequired()])
    payment_status = SelectField('Estado de Pago', choices=[(status.name, status.value) for status in PaymentStatus], validators=[DataRequired()])
    submit = SubmitField('Guardar')
    
    def validate_policy_number(self, field):
        """
        Valida que el número de póliza sea único, excluyendo la póliza actual si es una edición.
        """
        # Verificar si es una edición (id existe) o creación nueva
        if self.id.data:
            # Es una edición - excluir la póliza actual de la validación
            policy = Policy.query.filter(
                Policy.policy_number == field.data,
                Policy.id != int(self.id.data)
            ).first()
            
            if policy is not None:
                raise ValidationError('Este número de póliza ya está registrado. Por favor use uno diferente.')
        else:
            # Es una creación nueva - verificar si el número de póliza existe
            policy = Policy.query.filter_by(policy_number=field.data).first()
            if policy is not None:
                raise ValidationError('Este número de póliza ya está registrado. Por favor use uno diferente.')

class ProductForm(FlaskForm):
    id = HiddenField('ID')  # Campo oculto para guardar el ID del producto
    name = StringField('Nombre', validators=[DataRequired()])
    description = TextAreaField('Descripción')
    aseguradora = StringField('Aseguradora')
    commission_percentage = DecimalField('Porcentaje de Comisión', 
                                       validators=[DataRequired(), 
                                                 NumberRange(min=0, max=100)],
                                       default=0)
    sobrecomision = BooleanField('Sobrecomisión')
    override_percentage = DecimalField('Porcentaje de Sobrecomisión',
                                     validators=[Optional(), 
                                               NumberRange(min=0, max=100)],
                                     default=0)
    image = FileField('Imagen del Producto', 
                     validators=[
                         Optional(),
                         FileAllowed(['jpg', 'png', 'jpeg'], 'Solo imágenes (.jpg, .png, .jpeg)')
                     ])
    submit = SubmitField('Guardar')

class AgentForm(FlaskForm):
    id = HiddenField('ID')
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=50)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[Optional(), Length(min=6)])
    name = StringField('Nombre Completo', validators=[DataRequired()])
    phone = StringField('Teléfono', validators=[Optional()])
    address = StringField('Dirección', validators=[Optional()])
    date_of_birth = DateField('Fecha de Nacimiento', validators=[Optional()])
    hire_date = DateField('Fecha de Contratación', validators=[Optional()])
    document_type = SelectField('Tipo de Documento', choices=[(t.name, t.value) for t in DocumentType], validators=[DataRequired()])
    document_number = StringField('Número de Documento', validators=[DataRequired()])
    parent_id = SelectField('Supervisor', coerce=int, validators=[Optional()])
    submit = SubmitField('Guardar')

    def __init__(self, *args, **kwargs):
        super(AgentForm, self).__init__(*args, **kwargs)
        # Obtener todos los agentes existentes para el selector de supervisor
        agents = User.query.filter_by(role=UserRole.AGENTE).all()
        self.parent_id.choices = [(0, 'Sin Supervisor')] + [(agent.id, agent.name or agent.username) for agent in agents]

    def validate_username(self, username):
        if not self.id.data:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Por favor, use un nombre de usuario diferente.')
        else:
            user = User.query.filter_by(username=username.data).first()
            if user is not None and str(user.id) != self.id.data:
                raise ValidationError('Por favor, use un nombre de usuario diferente.')

    def validate_email(self, email):
        if not self.id.data:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Por favor, use una dirección de correo electrónico diferente.')
        else:
            user = User.query.filter_by(email=email.data).first()
            if user is not None and str(user.id) != self.id.data:
                raise ValidationError('Por favor, use una dirección de correo electrónico diferente.')

class SMTPConfigForm(FlaskForm):
    mail_server = StringField('Servidor SMTP', validators=[DataRequired()])
    mail_port = IntegerField('Puerto SMTP', validators=[DataRequired()])
    mail_use_tls = BooleanField('Usar TLS')
    mail_use_ssl = BooleanField('Usar SSL')
    mail_username = StringField('Nombre de Usuario SMTP', validators=[DataRequired()])
    mail_password = PasswordField('Contraseña SMTP', validators=[DataRequired()])
    mail_default_sender = StringField('Remitente por Defecto', validators=[DataRequired(), Email()])
    submit = SubmitField('Guardar Configuración')
