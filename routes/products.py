from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, session
from flask_login import login_required
from models import Product, db
from forms import ProductForm
from decorators import admin_required, admin_or_digitador_required
from utils.image_handler import ImageHandler
from utils.url_helpers import get_return_url
from PIL import Image
from io import BytesIO
from pathlib import Path

bp = Blueprint('products', __name__, url_prefix='/products')

@bp.route('/')
@login_required
@admin_or_digitador_required
def list_products():
    # Hacer la sesión permanente al entrar a esta vista
    session.permanent = True
    
    # Guardar/recuperar parámetros de paginación, filtros y ordenamiento en la sesión
    session_key = 'products_list_params'
    
    # Si hay parámetros en la solicitud, actualizar la sesión
    if request.args:
        # Limpiar la sesión si se hace una nueva búsqueda (cuando hay parámetros pero no hay page)
        if 'name' in request.args and 'page' not in request.args:
            if session_key in session:
                session.pop(session_key)
                
        # Guardar los parámetros actuales en la sesión
        session[session_key] = {
            'name': request.args.get('name', ''),
            'sort_by': request.args.get('sort_by', 'name'),
            'sort_order': request.args.get('sort_order', 'asc'),
            'page': request.args.get('page', 1, type=int),
            'per_page': request.args.get('per_page', 10, type=int)
        }
    
    # Si no hay parámetros pero sí hay sesión guardada, recuperarla para mantener el estado
    elif session_key in session:
        return redirect(url_for('products.list_products', **session[session_key]))
    
    # Obtener los parámetros ya sea de la solicitud o de la sesión
    params = session.get(session_key, {})
    name = params.get('name', request.args.get('name', ''))
    
    # Parámetros de ordenamiento
    sort_by = params.get('sort_by', request.args.get('sort_by', 'name'))
    sort_order = params.get('sort_order', request.args.get('sort_order', 'asc'))
    
    # Mapeo de nombres de parámetros a atributos de modelo para ordenamiento
    sort_columns = {
        'name': Product.name,
        'description': Product.description
    }
    
    query = Product.query
    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))
    
    # Aplicar ordenamiento
    if sort_by in sort_columns:
        if sort_order == 'desc':
            query = query.order_by(sort_columns[sort_by].desc())
        else:
            query = query.order_by(sort_columns[sort_by].asc())
    else:
        # Ordenamiento por defecto
        query = query.order_by(Product.name)
    
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
    
    return render_template('products/list.html', 
                         products=pagination.items, 
                         pagination=pagination,
                         title="Lista de Productos",
                         sort_by=sort_by,
                         sort_order=sort_order)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_product():
    form = ProductForm()
    if form.validate_on_submit():
        try:
            # Crear producto
            product = Product(
                name=form.name.data,
                description=form.description.data,
                aseguradora=form.aseguradora.data,
                commission_percentage=form.commission_percentage.data,
                sobrecomision=form.sobrecomision.data,
                override_percentage=form.override_percentage.data
            )

            # Manejar imagen si se proporcionó una
            if form.image.data:
                image_handler = ImageHandler()
                product.image_url = image_handler.save_product_image(form.image.data)

            db.session.add(product)
            db.session.commit()
            
            flash('Producto creado exitosamente', 'success')
            return redirect(get_return_url(url_for('products.list_products')))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el producto: {str(e)}', 'error')

    return render_template('products/create.html', form=form)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    # Establecer el ID del producto para la validación
    form.id.data = str(product.id)
    
    if form.validate_on_submit():
        try:
            # Actualizar datos básicos
            form.populate_obj(product)
            
            # Manejar nueva imagen si se proporcionó una
            if form.image.data:
                image_handler = ImageHandler()
                # Eliminar imagen anterior si existe
                if product.image_url:
                    image_handler.delete_product_image(product.image_url)
                # Guardar nueva imagen
                product.image_url = image_handler.save_product_image(form.image.data)
                
            db.session.commit()
            flash('Producto actualizado exitosamente', 'success')
            return redirect(get_return_url(url_for('products.list_products')))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el producto: {str(e)}', 'error')
    
    return render_template('products/edit.html', form=form, product=product)

@bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    try:
        # Eliminar imagen si existe
        if product.image_url:
            image_handler = ImageHandler()
            image_handler.delete_product_image(product.image_url)
            
        db.session.delete(product)
        db.session.commit()
        flash('Producto eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el producto: {str(e)}', 'error')
    
    return redirect(get_return_url(url_for('products.list_products')))

@bp.route('/image/<filename>')
def serve_image(filename):
    size = request.args.get('size')
    
    # Definir tamaños permitidos
    sizes = {
        'thumbnail': (100, 100),
        'medium': (300, 300)
    }
    
    try:
        # Abrir imagen original
        base_path = Path('/app/static/img/products')
        image_path = base_path / filename
        default_path = base_path / 'default.jpg'
        
        # Si la imagen solicitada no existe o hay error, usar la imagen por defecto
        try:
            if not image_path.exists():
                if not default_path.exists():
                    # Si no existe la imagen por defecto, crearla
                    img = Image.new('RGB', (300, 300), color='lightgray')
                    img.save(default_path, 'JPEG')
                image_path = default_path
                
            img = Image.open(image_path)
            
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar si se especificó un tamaño
            if size in sizes:
                img.thumbnail(sizes[size], Image.Resampling.LANCZOS)
            
            # Servir imagen desde memoria
            img_io = BytesIO()
            img.save(img_io, 'JPEG', quality=85)
            img_io.seek(0)
            
            response = send_file(img_io, mimetype='image/jpeg')
            response.headers['Cache-Control'] = 'public, max-age=31536000'  # Cache por 1 año
            return response
            
        except Exception as inner_e:
            print(f"Error interno al servir imagen {filename}: {str(inner_e)}")
            # Crear y servir una imagen por defecto en memoria
            img = Image.new('RGB', (300, 300), color='lightgray')
            img_io = BytesIO()
            img.save(img_io, 'JPEG', quality=85)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg')
            
    except Exception as e:
        print(f"Error al servir imagen {filename}: {str(e)}")
        # Si hay cualquier error, crear y servir una imagen por defecto en memoria
        img = Image.new('RGB', (300, 300), color='lightgray')
        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=85)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/jpeg')
