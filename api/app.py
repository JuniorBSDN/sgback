# Arquivo: app.py

from flask import Flask, send_from_directory, g, request, jsonify
from services.firestore_service import initialize_firestore  # Importa a função de inicialização
from routes import register_blueprints  # Importa a função de registro de Blueprints
from config import Config  # Importa a configuração (para SECRET_KEY)
# NOVO: Importações para validação JWT
import jwt
import os

# --- 1. INICIALIZAÇÃO DO FLASK ---

# O 'static_folder='.' permite que o Flask sirva os arquivos HTML, JS e CSS estáticos
# a partir do diretório raiz, o que é comum em arquiteturas simples de front-end/backend.
app = Flask(__name__, static_folder='.')
app.config.from_object(Config)  # Carrega as configurações (incluindo SECRET_KEY)

# 2. INICIALIZAÇÃO DO FIREBASE (Antes de registrar rotas que usam o DB)
db_status = initialize_firestore()
if db_status:
    print("✅ Aplicação Flask pronta. Firestore acessível via get_db().")
else:
    print("⚠️ Aplicação Flask rodando, mas Firestore não foi inicializado (Verifique FIRESTORE_PRIVATE_KEY_JSON).")


# 3. HOOK DE REQUISIÇÃO (CRÍTICO para a segurança e logs)
@app.before_request
def before_request():
    """
    Popula o objeto 'g' (global/request-local) com dados do usuário,
    AGORA validando o Token JWT enviado no cabeçalho 'Authorization: Bearer <token>'.
    """

    # 1. Obtém o cabeçalho de Autorização
    auth_header = request.headers.get('Authorization')
    token = None

    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]

    # Popula g com valores padrão (não autenticado)
    g.user_matricula = None
    g.user_permissao = None
    g.user_nome = None

    if token:
        try:
            # Tenta decodificar e validar o token usando a chave secreta
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])

            # Se a decodificação for bem-sucedida, extrai os dados do payload e popula 'g'
            g.user_matricula = payload.get('sub') # 'sub' (Subject) é a matrícula
            g.user_permissao = payload.get('permissao')
            # O nome do usuário não está no token, mas a matrícula é suficiente
            
        except jwt.ExpiredSignatureError:
            print("AVISO: Token JWT Expirado.")
        except jwt.InvalidTokenError:
            print("ERRO: Token JWT Inválido (Assinatura, formato ou chave errada).")
        except Exception as e:
            print(f"ERRO: Falha crítica na validação do JWT: {e}")


# 4. REGISTRO DOS BLUEPRINTS
register_blueprints(app)


# 5. ROTAS ESTÁTICAS PARA SERVIR ARQUIVOS HTML/CSS/JS (CRÍTICO para o Vercel)
@app.route('/')
def index():
    """Serve o arquivo principal (index.html)."""
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve os demais arquivos estáticos (pdv.html, produto.html, etc.)."""
    return send_from_directory('.', filename)
