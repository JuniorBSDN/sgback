import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env localmente (IGNORADO pelo Git)
load_dotenv()


class Config:
    """Configurações de ambiente, credenciais e chaves."""

    # Chave Secreta do Flask (para sessions, etc.)
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'default_secret_dev_key')

    # Credenciais do Firestore
    # CRÍTICO: Na Vercel, a chave JSON deve ser armazenada como variável de ambiente
    FIRESTORE_PRIVATE_KEY_JSON = os.environ.get('FIRESTORE_PRIVATE_KEY_JSON')

    # NOVO: Chave Secreta para Assinatura do JWT (Usada para gerar e validar tokens)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'chave_secreta_padrao_para_desenvolvimento')

    # Configurações de Integração
    # URLs de APIs externas (SIMULADAS)
    PAYMENT_GATEWAY_URL = os.environ.get('PAYMENT_GATEWAY_URL', 'http://simulador.pagamento.com/api/charge')
    NFE_EMITTER_URL = os.environ.get('NFE_EMITTER_URL', 'http://simulador.nfe.com/api/emitir')

