# Arquivo: routes/auth_routes.py

from flask import Blueprint, request, jsonify, g
from functools import wraps
from werkzeug.security import check_password_hash  # NOVO IMPORT NECESSÁRIO

# Importa as funções de serviço (incluindo a nova de busca)
from services.firestore_service import log_auditoria, find_user_by_matricula

# Criação do Blueprint para as rotas de autenticação
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def auth_required(f):
    """Decorator para exigir autenticação por token nos endpoints."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simplesmente verificamos se as informações do usuário estão no objeto global (g)
        # O g é populado em um hook da aplicação ou, no seu caso, pelo frontend
        # que passa a matrícula e permissão na URL ou Header (em um sistema real).

        # Para fins práticos e de teste, usaremos um campo 'user_matricula' no g
        # Se for um sistema real, o JWT faria essa verificação.

        # NOTE: Em sistemas reais, a autenticação seria feita via JWT, mas para
        # simulação de um ERP, verificamos se a matrícula foi populada.
        if not getattr(g, 'user_matricula', None):
            return jsonify({"message": "Autenticação necessária.", "success": False}), 401

        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Realiza o login verificando as credenciais no Firestore.
    """
    data = request.get_json()
    matricula = data.get('matricula')
    senha_digitada = data.get('senha')

    if not matricula or not senha_digitada:
        return jsonify({"message": "Matrícula e senha são obrigatórias.", "success": False}), 400

    # 1. Busca o usuário no Firestore
    user_data = find_user_by_matricula(matricula)

    if not user_data:
        log_auditoria(matricula, 'Autenticação', 'Falha Login', 'Matrícula inexistente.')
        return jsonify({"message": "Matrícula ou senha inválida.", "success": False}), 401

    # 2. Verifica a senha (CRÍTICO: Deve-se usar HASH!)
    senha_hash = user_data.get('senha_hash')

    if not senha_hash:
        log_auditoria(matricula, 'Autenticação', 'Falha Login', 'Usuário sem hash de senha no DB.')
        return jsonify({"message": "Erro de configuração de segurança (hash ausente).", "success": False}), 500

    try:
        # Usa check_password_hash para segurança (requer a biblioteca werkzeug)
        if check_password_hash(senha_hash, senha_digitada):
            # Login bem-sucedido
            log_auditoria(matricula, 'Autenticação', 'Login Sucesso')

            # Retorna os dados necessários para o frontend (index.html)
            return jsonify({
                "message": "Login bem-sucedido.",
                "success": True,
                "user_matricula": matricula,
                "user_nome": user_data.get('nome', matricula),
                "user_permissao": user_data.get('acesso', 'Operador')  # Ex: 'Admin', 'Gerente', 'Operador'
            }), 200
        else:
            # Senha incorreta
            log_auditoria(matricula, 'Autenticação', 'Falha Login', 'Senha incorreta.')
            return jsonify({"message": "Matrícula ou senha inválida.", "success": False}), 401
    except ValueError:
        # Se o hash estiver mal formatado ou o check_password_hash falhar por erro de formato
        log_auditoria(matricula, 'Autenticação', 'Erro Hash', 'Formato de hash de senha inválido.')
        return jsonify({"message": "Erro de segurança interno.", "success": False}), 500
    except Exception as e:
        log_auditoria(matricula, 'Autenticação', 'Erro DB', f'Erro ao verificar senha: {e}')
        return jsonify({"message": "Erro interno do servidor.", "success": False}), 500