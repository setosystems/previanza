from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import Product, db
from forms import ProductForm
from decorators import admin_required, admin_or_digitador_required
import os
from werkzeug.utils import secure_filename
from PIL import Image

bp = Blueprint('products', __name__, url_prefix='/products')

def save_product_image(form_image):
    """Guarda la imagen del producto y retorna la ruta relativa"""
    if not form_image:
        return None
        
    # Crear directorio si no existe
    upload_path = os.path.join('static', 'img', 'products')
    os.makedirs(upload_path, exist_ok=True)
    
    # Generar nombre de archivo seguro
    filename = secure_filename(form_image.filename)
    file_path = os.path.join(upload_path, filename)
    
    # Guardar y optimizar imagen
    image = Image.open(form_image)
    image = image.convert('RGB')  # Convertir a RGB si es necesario
    
    # Redimensionar si es muy grande
    if image.size[0] > 800 or image.size[1] > 600:
        image.thumbnail((800, 600))
    
    # Guardar con calidad optimizada
    image.save(file_path, 'JPEG', quality=85, optimize=True)
    
    # Retornar ruta relativa para la base de datos
    return os.path.join('img', 'products', filename)

@bp.route('/')
@login_required
@admin_or_digitador_required
def list_products():
    name = request.args.get('name', '')
    
    query = Product.query
    if name:
        query = query.filter(Product.name.ilike(f'%{name}%'))
    
    products = query.all()
    return render_template('products/list.html', products=products)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def create_product():
    form = ProductForm()
    if form.validate_on_submit():
        # Procesar la imagen si se proporcionó una
        image_path = save_product_image(form.image.data) if form.image.data else None
        
        product = Product(
            name=form.name.data,
            description=form.description.data,
            aseguradora=form.aseguradora.data,
            sobrecomision=form.sobrecomision.data,
            commission_percentage=form.commission_percentage.data,
            override_percentage=form.override_percentage.data if form.sobrecomision.data else 0,
            image_url=image_path
        )
        db.session.add(product)
        db.session.commit()
        flash('Producto creado exitosamente.')
        return redirect(url_for('products.list_products'))
    return render_template('products/create.html', form=form)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_or_digitador_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        # Procesar la imagen si se proporcionó una nueva
        if form.image.data:
            # Eliminar imagen anterior si existe
            if product.image_url:
                old_image_path = os.path.join('static', product.image_url)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Guardar nueva imagen
            image_path = save_product_image(form.image.data)
            product.image_url = image_path
        
        form.populate_obj(product)
        if not form.sobrecomision.data:
            product.override_percentage = 0
            
        db.session.commit()
        flash('Producto actualizado exitosamente.')
        return redirect(url_for('products.list_products'))
        
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
