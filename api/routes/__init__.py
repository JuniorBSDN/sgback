# Arquivo: routes/__init__.py

from flask import Flask

# Importa os Blueprints definidos nos arquivos de rota
from .auth_routes import auth_bp
from .erp_routes import erp_bp

def register_blueprints(app: Flask):
    """
    Registra todos os Blueprints da aplicação no objeto Flask principal.

    :param app: A instância principal da aplicação Flask.
    """
    # Rotas de Autenticação (login, logout, etc.)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Rotas de Módulos do ERP (vendas, produto, recebimento, etc.)
    app.register_blueprint(erp_bp, url_prefix='/api/erp')

# Este arquivo é essencial para que o diretório 'routes' seja reconhecido como um pacote Python.