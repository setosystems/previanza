from PIL import Image
import os
from pathlib import Path
import uuid
from io import BytesIO
from flask import url_for

class ImageHandler:
    def __init__(self):
        self.base_path = Path('static/img/products')
        # Crear directorio si no existe
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_product_image(self, image_file):
        """Guarda una imagen de producto optimizada"""
        if not image_file:
            return None

        try:
            # Generar nombre único
            ext = image_file.filename.rsplit('.', 1)[1].lower()
            if ext not in ['jpg', 'jpeg', 'png']:
                raise ValueError("Formato de imagen no soportado")
                
            filename = f"{uuid.uuid4()}.jpg"  # Siempre convertimos a JPG

            # Procesar imagen
            img = Image.open(image_file)
            
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Redimensionar si es muy grande (máximo 800px en cualquier dimensión)
            if img.size[0] > 800 or img.size[1] > 800:
                img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                
            # Guardar con optimización
            save_path = self.base_path / filename
            img.save(save_path, 'JPEG', quality=85, optimize=True)
            
            return str(Path('img/products') / filename)
            
        except Exception as e:
            print(f"Error al guardar imagen: {str(e)}")
            return None

    def delete_product_image(self, image_url):
        """Elimina una imagen de producto"""
        if not image_url:
            return

        try:
            image_path = self.base_path / Path(image_url).name
            if image_path.exists():
                image_path.unlink()
        except Exception as e:
            print(f"Error al eliminar imagen: {str(e)}")

    def get_image_url(self, image_url, size=None):
        """
        Genera URL para la imagen con el tamaño especificado
        size puede ser 'thumbnail' (100x100) o 'medium' (300x300)
        """
        if not image_url:
            return url_for('static', filename='img/products/default.jpg')
            
        try:
            image_path = self.base_path / Path(image_url).name
            if not image_path.exists():
                return url_for('static', filename='img/products/default.jpg')
                
            return url_for('products.serve_image', 
                          filename=Path(image_url).name, 
                          size=size) if size else url_for('static', filename=image_url)
        except:
            return url_for('static', filename='img/products/default.jpg') 