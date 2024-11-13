import subprocess
import os

def compile_tailwind():
    try:
        # Asegurarse de que el directorio static/css existe
        os.makedirs('static/css', exist_ok=True)
        
        # Compilar Tailwind
        subprocess.run([
            'tailwindcss',
            '-i', 'static/css/input.css',
            '-o', 'static/css/output.css',
            '--minify'
        ], check=True)
        print("Tailwind CSS compilado exitosamente")
    except subprocess.CalledProcessError as e:
        print(f"Error al compilar Tailwind CSS: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    compile_tailwind() 