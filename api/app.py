# Arquivo: app.py

from flask import Flask, send_from_directory, g, request, jsonify
from services.firestore_service import initialize_firestore  # Importa a função de inicialização
from routes import register_blueprints  # Importa a função de registro de Blueprints
from config import Config  # Importa a configuração (para SECRET_KEY)
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
    Popula o objeto 'g' (global/request-local) com dados do usuário que o
    frontend envia nos headers, simulando a extração de um JWT.

    Isso é o que permite que o @auth_required funcione e que o log_auditoria
    saiba quem está fazendo a ação (g.user_matricula).
    """

    # Tentativa de obter dados dos headers (o frontend deve enviá-los após o login)
    matricula = request.headers.get('X-User-Matricula')
    permissao = request.headers.get('X-User-Permissao')
    nome = request.headers.get('X-User-Nome', matricula)  # Nome opcional

    # Popula o objeto 'g'
    g.user_matricula = matricula
    g.user_permissao = permissao
    g.user_nome = nome

    # Opcional: Logar requisições para debug
    # print(f"Requisição recebida. Usuário: {matricula}, Permissão: {permissao}, Rota: {request.path}")


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

    # Garante que ele procure no diretório raiz do projeto.
    # Esta rota é genérica e deve ser a última a ser verificada.
    return send_from_directory('.', filename)


# 6. Variável 'application' usada pelo servidor WSGI (Vercel/Gunicorn)
application = app

if __name__ == '__main__':
    # Roda em ambiente local de desenvolvimento
    app.run(debug=True, port=os.environ.get('PORT', 8000))
