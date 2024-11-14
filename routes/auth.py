from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from forms import LoginForm, RegistrationForm, UserEditForm, RequestResetForm, ResetPasswordForm
from models import User, db, UserRole, DocumentType
from decorators import admin_required
from flask_mail import Message
from extensions import mail
from smtplib import SMTPException
import logging

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña inválidos')
            return redirect(url_for('auth.login'))
            
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page if next_page else url_for('index'))
        
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@bp.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    form = RegistrationForm()
    form.parent_id.choices = [(0, 'Ninguno')] + [(u.id, u.username) for u in User.query.filter_by(role=UserRole.AGENTE).all()]
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=UserRole[form.role.data],
            document_type=DocumentType[form.document_type.data],
            document_number=form.document_number.data,
            name=form.name.data,
            phone=form.phone.data,
            address=form.address.data,
            date_of_birth=form.date_of_birth.data,
            hire_date=form.hire_date.data,
            parent_id=form.parent_id.data if form.parent_id.data != 0 else None
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Felicidades, el nuevo usuario ha sido registrado!')
        return redirect(url_for('auth.list_users'))
    return render_template('register.html', title='Registro', form=form)

@bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    form.parent_id.choices = [(0, 'Ninguno')] + [(u.id, u.username) for u in User.query.filter_by(role=UserRole.AGENTE).all() if u.id != user_id]
    
    form.role.data = user.role.name
    
    if form.validate_on_submit():
        form.populate_obj(user)
        user.role = UserRole[form.role.data]
        user.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        db.session.commit()
        flash('Usuario actualizado exitosamente')
        return redirect(url_for('auth.list_users'))
    
    return render_template('auth/edit_user.html', form=form, user=user)

@bp.route('/users')
@login_required
@admin_required
def list_users():
    users = User.query.all()
    return render_template('auth/users.html', users=users)

@bp.route('/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('No puedes eliminar tu propio usuario')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('Usuario eliminado exitosamente')
    return redirect(url_for('auth.list_users'))

@bp.route('/change_role/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        new_role = request.form.get('role')
        if new_role in [role.name for role in UserRole]:
            user.role = UserRole[new_role]
            db.session.commit()
            flash(f'Rol de usuario actualizado a {new_role}')
            return redirect(url_for('auth.list_users'))
        else:
            flash('Rol inválido')
    return render_template('auth/change_role.html', user=user, roles=UserRole)

@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            try:
                token = user.generate_reset_token()
                send_password_reset_email(user, token)
                flash('Se han enviado instrucciones para restablecer tu contraseña por correo electrónico.', 'info')
            except SMTPException as e:
                logging.error(f"SMTP error occurred: {str(e)}")
                flash('Ocurrió un error al enviar el correo electrónico. Por favor, inténtalo de nuevo más tarde o contacta al administrador.', 'error')
            except Exception as e:
                logging.error(f"Unexpected error occurred: {str(e)}")
                flash('Ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde o contacta al administrador.', 'error')
        else:
            logging.warning(f"Password reset attempted for non-existent email: {form.email.data}")
            flash('No se encontró una cuenta con ese correo electrónico.', 'warning')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html', title='Restablecer Contraseña', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.filter_by(reset_password_token=token).first()
    
    if not user:
        flash('El enlace para restablecer la contraseña es inválido.')
        return redirect(url_for('auth.reset_password_request'))
    
    try:
        if not user.verify_reset_token(token):
            flash('El enlace para restablecer la contraseña ha expirado.')
            return redirect(url_for('auth.reset_password_request'))
    except Exception as e:
        logging.error(f"Error verificando token: {str(e)}")
        flash('Ocurrió un error al verificar el token.')
        return redirect(url_for('auth.reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_password_token = None
        user.reset_password_expiration = None
        db.session.commit()
        flash('Tu contraseña ha sido restablecida.')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)

def send_password_reset_email(user, token):
    msg = Message('Restablecer Contraseña',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f'''Para restablecer tu contraseña, visita el siguiente enlace:
{url_for('auth.reset_password', token=token, _external=True)}

Si no solicitaste restablecer tu contraseña, ignora este mensaje.
'''
    logging.info(f"Attempting to send password reset email with the following SMTP configuration:")
    logging.info(f"MAIL_SERVER: {current_app.config['MAIL_SERVER']}")
    logging.info(f"MAIL_PORT: {current_app.config['MAIL_PORT']}")
    logging.info(f"MAIL_USE_TLS: {current_app.config['MAIL_USE_TLS']}")
    logging.info(f"MAIL_USE_SSL: {current_app.config['MAIL_USE_SSL']}")
    logging.info(f"MAIL_USERNAME: {current_app.config['MAIL_USERNAME']}")
    logging.info(f"MAIL_DEFAULT_SENDER: {current_app.config['MAIL_DEFAULT_SENDER']}")
    
    try:
        mail.send(msg)
        logging.info(f"Password reset email sent successfully to {user.email}")
    except SMTPException as e:
        logging.error(f"SMTP error occurred while sending password reset email: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error occurred while sending password reset email: {str(e)}")
        raise

def create_user(username, email, password, role):
    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
    return None

def create_agent_test_user():
    agent_user = create_user('agent_test', 'agent_test@example.com', 'agent123', UserRole.AGENTE)
    if agent_user:
        print("Usuario de prueba (agente) creado exitosamente")
    else:
        print("No se pudo crear el usuario de prueba (agente). El nombre de usuario podría ya existir.")
