from app import create_app
from models import db

app = create_app()

def reset_database():
    with app.app_context():
        # Eliminar todas las tablas
        db.drop_all()
        print("Tablas eliminadas")
        
        # Crear todas las tablas nuevamente
        db.create_all()
        print("Tablas recreadas")

if __name__ == "__main__":
    reset_database() 