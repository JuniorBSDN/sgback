# Arquivo: routes/auth_routes.py

from flask import Blueprint, request, jsonify, g
from functools import wraps
from werkzeug.security import check_password_hash  # CRÍTICO: Importa a função de segurança

# Importa as funções de serviço (incluindo a nova de busca e log)
from services.firestore_service import log_auditoria, find_user_by_matricula

# Criação do Blueprint para as rotas de autenticação
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def auth_required(f):
    """
    Decorator para exigir autenticação. Verifica se o usuário logado está no objeto 'g'.
    NOTA: O 'g' é populado no hook @app.before_request do app.py.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se a matrícula do usuário foi populada no objeto global de request 'g'
        if not getattr(g, 'user_matricula', None):
            return jsonify({"message": "Autenticação necessária. Matrícula ausente no Header.", "success": False}), 401

        return f(*args, **kwargs)

    return decorated_function


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Realiza o login verificando as credenciais (Matrícula e Senha-Hash) no Firestore.
    """
    data = request.get_json()
    matricula = data.get('matricula')
    senha_digitada = data.get('senha')

    if not matricula or not senha_digitada:
        log_auditoria('DESCONHECIDO', 'Autenticação', 'Erro Validação', 'Matrícula ou senha ausente.')
        return jsonify({"message": "Matrícula e senha são obrigatórias.", "success": False}), 400

    # 1. Busca o usuário no Firestore pela Matrícula (que é o ID do documento)
    user_data = find_user_by_matricula(matricula)

    if not user_data:
        log_auditoria(matricula, 'Autenticação', 'Falha Login', 'Matrícula inexistente.')
        return jsonify({"message": "Matrícula ou senha inválida.", "success": False}), 401

    # 2. Verifica a Senha: Compara a senha digitada com o HASH armazenado no DB
    senha_hash = user_data.get('senha_hash')

    if not senha_hash:
        log_auditoria(matricula, 'Autenticação', 'Falha Login', 'Usuário sem hash de senha no DB.')
        return jsonify({"message": "Erro de segurança: Hash de senha ausente.", "success": False}), 500

    try:
        if check_password_hash(senha_hash, senha_digitada):
            # Login bem-sucedido
            log_auditoria(matricula, 'Autenticação', 'Login Sucesso')

            # Retorna dados essenciais para o Frontend salvar no sessionStorage
            return jsonify({
                "message": "Login bem-sucedido.",
                "success": True,
                "user_matricula": matricula,
                "user_nome": user_data.get('nome', matricula),
                # Nível de Acesso: 'Admin', 'Gerente', 'Operador'
                "user_permissao": user_data.get('acesso', 'Operador')
            }), 200
        else:
            # Senha incorreta
            log_auditoria(matricula, 'Autenticação', 'Falha Login', 'Senha incorreta.')
            return jsonify({"message": "Matrícula ou senha inválida.", "success": False}), 401
    except Exception as e:
        log_auditoria(matricula, 'Autenticação', 'Erro Crítico', f'Falha na verificação de hash: {e}')
        return jsonify({"message": "Erro interno do servidor.", "success": False}), 500
