from app import create_app
from models import db, Product
from sqlalchemy.exc import ProgrammingError

app = create_app()

def update_product_images():
    with app.app_context():
        try:
            # Mapeo de productos a imágenes
            image_mapping = {
                'Seguro de Vida': 'img/products/vida.jpg',
                'Seguro de Salud': 'img/products/salud.jpg',
                'Seguro de Auto': 'img/products/auto.jpg',
                'Seguro de Hogar': 'img/products/hogar.jpg',
                'Seguro de Accidentes': 'img/products/accidentes.jpg',
                'Seguro de Viaje': 'img/products/viaje.jpg',
                'Seguro PYMES': 'img/products/pymes.jpg',
                'Seguro Jubilación': 'img/products/jubilacion.jpg',
                'Seguro Educación': 'img/products/educacion.jpg',
                'Hogar 360': 'img/products/hogar360.jpg',
                'Seguro Inundación': 'img/products/inundacion.jpg',
                'Seguro Mascotas': 'img/products/mascotas.jpg'
            }

            products = Product.query.all()
            for product in products:
                if product.name in image_mapping:
                    product.image_url = image_mapping[product.name]
                else:
                    product.image_url = 'img/products/default.jpg'
            
            db.session.commit()
            print("Imágenes de productos actualizadas")
        except ProgrammingError as e:
            if "relation" in str(e) and "does not exist" in str(e):
                print("La tabla de productos aún no existe. Saltando actualización de imágenes.")
            else:
                raise e

if __name__ == "__main__":
    update_product_images() 