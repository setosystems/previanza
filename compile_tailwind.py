import subprocess
import os
import logging

def compile_tailwind():
    try:
        # Asegurarse de que el directorio static/css existe
        os.makedirs('static/css', exist_ok=True)
        
        # Compilar Tailwind
        subprocess.run([
            'tailwindcss',
            '-i', 'static/css/input.css',
            '-o', 'static/css/output.css',
            '--minify',
            '--quiet'
        ], check=True, capture_output=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if os.environ.get('FLASK_DEBUG') == '1':
            logging.info("Tailwind CSS compilado exitosamente")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error al compilar Tailwind CSS: {e}")
    except Exception as e:
        logging.error(f"Error inesperado: {e}")

if __name__ == "__main__":
    compile_tailwind() 