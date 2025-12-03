# Arquivo: app.py
from flask import Flask, send_from_directory, g, request, jsonify
from services.firestore_service import initialize_firestore  # Importa a função de inicialização
from routes import register_blueprints  # Importa a função de registro de Blueprints
from config import Config  # Importa a configuração (para SECRET_KEY)

# --- 1. INICIALIZAÇÃO DO FLASK ---

# O 'static_folder='.' permite que o Flask sirva os arquivos HTML, JS e CSS estáticos.
app = Flask(__name__, static_folder='.')
app.config.from_object(Config)  # Carrega as configurações (incluindo SECRET_KEY)

# 2. INICIALIZAÇÃO DO FIREBASE
db_status = initialize_firestore()
if db_status:
    print("✅ Aplicação Flask pronta. Firestore acessível via get_db().")
else:
    print("⚠️ Aplicação Flask rodando, mas Firestore não foi inicializado.")


# 3. HOOK DE REQUISIÇÃO (CRÍTICO para passar dados do usuário logado)
@app.before_request
def before_request():
    """
    Popula o objeto 'g' (global/request-local) com dados do usuário
    para que as rotas possam usá-los (ex: log_auditoria e auth_required).
    """
    # Para simulação do ERP, o frontend está passando a matrícula e permissão
    # no header ou query param (em um sistema real, seria via JWT).

    # Tentativa de obter dados do header (mais seguro que query params)
    matricula = request.headers.get('X-User-Matricula')
    permissao = request.headers.get('X-User-Permissao')
    nome = request.headers.get('X-User-Nome', matricula)  # Nome opcional

    # O objeto 'g' estará disponível para o restante do ciclo da requisição
    g.user_matricula = matricula
    g.user_permissao = permissao
    g.user_nome = nome


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


# Variável usada pelo servidor WSGI (Vercel)
application = app

if __name__ == '__main__':
    # Roda em ambiente local de desenvolvimento
    app.run(debug=True, port=8000)