from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required
from models import Product, db
from forms import ProductForm
from decorators import admin_required, admin_or_digitador_required
from utils.image_handler import ImageHandler
from PIL import Image
from io import BytesIO
from pathlib import Path

bp = Blueprint('products', __name__, url_prefix='/products')

@bp.route('/')
@login_required
@admin_or_digitador_required
def list_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Product.query.order_by(Product.name)
    
    # Aplicar filtros de búsqueda si existen
    name = request.args.get('name', '')
    aseguradora = request.args.get('aseguradora', '')
    
    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))
    if aseguradora:
        query = query.filter(Product.aseguradora.ilike(f'%{aseguradora}%'))
    
    # Obtener la paginación
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    total = query.count()
    products = pagination.items
    
    return render_template('products/list.html',
                         products=products,
                         pagination=pagination,
                         total=total,
                         page=page,
                         per_page=per_page)

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
                override_commission_percentage=form.override_commission_percentage.data
            )

            # Manejar imagen si se proporcionó una
            if form.image.data:
                image_handler = ImageHandler()
                product.image_url = image_handler.save_product_image(form.image.data)

            db.session.add(product)
            db.session.commit()
            
            flash('Producto creado exitosamente', 'success')
            return redirect(url_for('products.list_products'))
            
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
            return redirect(url_for('products.list_products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el producto: {str(e)}', 'error')
    
    return render_template('products/edit.html', form=form, product=product)

@bp.route('/delete/<int:id>')
@login_required
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Producto eliminado exitosamente.')
    return redirect(url_for('products.list_products'))

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
