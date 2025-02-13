from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, DateField, HiddenField, IntegerField, BooleanField, DecimalField, EmailField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, Length, NumberRange
from models import User, UserRole, DocumentType, EmisionStatus, PaymentStatus

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
    document_type = SelectField('Tipo de Documento', choices=[(dt.name, dt.value) for dt in DocumentType], validators=[DataRequired()])  # Campo agregado
    document_number = StringField('Número de Documento', validators=[DataRequired()])  # Campo agregado

    submit = SubmitField('Guardar Cambios')

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.original_username = kwargs.get('obj', None).username if kwargs.get('obj', None) else None
        self.original_email = kwargs.get('obj', None).email if kwargs.get('obj', None) else None

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Por favor, use un nombre de usuario diferente.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Por favor, use una dirección de correo electrónico diferente.')

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
    name = StringField('Nombre', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    phone = StringField('Teléfono', validators=[DataRequired()])
    address = StringField('Dirección')
    city = StringField('Ciudad')
    document_type = SelectField('Tipo de Documento', choices=[(dt.name, dt.value) for dt in DocumentType])
    document_number = StringField('Número de Documento', validators=[DataRequired()])
    birthdate = DateField('Fecha de Nacimiento', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Guardar')

    def validate_document_number(self, field):
        """
        Valida el número de documento según el tipo seleccionado.
        """
        if self.document_type.data == 'DNI':  # Si es cédula ecuatoriana
            if not validate_ecuador_id(field.data):
                raise ValidationError('El número de cédula ingresado no es válido. Verifique que sea una cédula ecuatoriana válida.')
        elif self.document_type.data == 'PASAPORTE':
            if len(field.data) < 6:
                raise ValidationError('El número de pasaporte debe tener al menos 6 caracteres.')
        elif self.document_type.data == 'CARNET_EXTRANJERIA':
            if not field.data.isalnum() or len(field.data) < 4:
                raise ValidationError('El número de carnet de extranjería no es válido.')

class PolicyForm(FlaskForm):
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

class ProductForm(FlaskForm):
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
