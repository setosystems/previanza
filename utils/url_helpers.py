from flask import request
from urllib.parse import urlencode

def get_return_url(endpoint, **kwargs):
    """
    Construye una URL de retorno preservando los parámetros de paginación y filtros.
    """
    # Parámetros base que queremos preservar
    params = {
        'page': request.args.get('page', '1'),
        'per_page': request.args.get('per_page', '10')
    }
    
    # Añadir parámetros de filtro si existen
    filter_params = ['name', 'email', 'document_type', 'document_number', 
                    'policy_number', 'client_name', 'product_name', 'aseguradora']
    
    for param in filter_params:
        value = request.args.get(param)
        if value:
            params[param] = value
    
    # Añadir parámetros adicionales
    params.update(kwargs)
    
    # Construir la URL con los parámetros
    return f"{endpoint}?{urlencode(params)}" 