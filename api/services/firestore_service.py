# Arquivo: services/firestore_service.py

import os
import json
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# Importa a configuração para obter a chave (CRÍTICO para o Vercel)
from config import Config

# Variável global para armazenar a instância do Firestore
db = None


def initialize_firestore():
    """
    Inicializa a conexão com o Firestore usando a chave JSON armazenada
    na variável de ambiente FIRESTORE_PRIVATE_KEY_JSON.
    """
    global db

    # Garante que a aplicação só inicialize uma vez
    if Config.FIRESTORE_PRIVATE_KEY_JSON and not firebase_admin._apps:
        try:
            # CRÍTICO: Decodifica a string JSON da variável de ambiente
            cred_data = json.loads(Config.FIRESTORE_PRIVATE_KEY_JSON)

            cred = credentials.Certificate(cred_data)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("INFO: Firestore inicializado com sucesso.")
        except json.JSONDecodeError:
            print("ERRO CRÍTICO: A variável FIRESTORE_PRIVATE_KEY_JSON está mal formatada. Verifique o Vercel.")
            db = None
        except Exception as e:
            print(f"ERRO: Falha ao inicializar Firestore: {e}")
            db = None
    elif not Config.FIRESTORE_PRIVATE_KEY_JSON:
        print("AVISO: Chave FIRESTORE_PRIVATE_KEY_JSON ausente. Usando ambiente local ou DB desativado.")
        db = None

    return db


def get_db():
    """Retorna a instância do DB, inicializando se necessário (Lazy Initialization)."""
    global db
    if db is None:
        db = initialize_firestore()
    return db


def log_auditoria(matricula, modulo, acao, detalhe=""):
    """Registra uma ação na coleção de auditoria_logs."""
    db_instance = get_db()
    if not db_instance:
        print(f"AVISO: Log de auditoria falhou. DB não inicializado: {modulo} - {acao}")
        return

    try:
        db_instance.collection('auditoria_logs').add({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'matricula': matricula,
            'modulo': modulo,
            'acao': acao,
            'detalhe': detalhe
        })
    except Exception as e:
        print(f"ERRO: Falha ao registrar log de auditoria: {e}")


# ==========================================================
# FUNÇÕES DE PRODUTO
# ==========================================================

def save_or_update_product(product_data):
    """
    Salva ou atualiza um produto na coleção 'produtos'.
    Usa o 'codigoBarra' como ID do documento.
    """
    db_instance = get_db()
    if not db_instance:
        return False, "Banco de dados não conectado."

    barcode = product_data.get('codigoBarra')
    if not barcode:
        return False, "Código de Barras ausente."

    # Adiciona/Atualiza a data da última modificação
    product_data['last_updated'] = firestore.SERVER_TIMESTAMP

    try:
        # Usa .set() com o ID do documento, e 'merge=True' para atualizar campos existentes
        db_instance.collection('produtos').document(barcode).set(product_data, merge=True)
        return True, "Produto salvo com sucesso."
    except Exception as e:
        print(f"ERRO ao salvar produto {barcode}: {e}")
        return False, f"Erro interno ao salvar produto: {e}"


def find_product_by_barcode(barcode):
    """Busca um produto pelo código de barras na coleção 'produtos'."""
    db_instance = get_db()
    if not db_instance:
        return None

    try:
        doc_ref = db_instance.collection('produtos').document(barcode)
        doc = doc_ref.get()

        if doc.exists:
            # Retorna o dicionário do produto
            return doc.to_dict()
        else:
            return None  # Produto não encontrado
    except Exception as e:
        print(f"ERRO ao buscar produto {barcode}: {e}")
        return None


# ==========================================================
# 🔑 FUNÇÃO DE USUÁRIO (CRÍTICO para AuthRoutes)
# ==========================================================

def find_user_by_matricula(matricula):
    """
    Busca um usuário pela matrícula na coleção 'usuarios'.
    Usada para carregar o HASH da senha para verificação de login.
    """
    db_instance = get_db()
    if not db_instance:
        return None

    try:
        # A matrícula é usada como ID do documento
        doc_ref = db_instance.collection('usuarios').document(matricula)
        doc = doc_ref.get()

        if doc.exists:
            # Retorna o dicionário do usuário, incluindo 'nome', 'acesso', 'senha_hash'
            return doc.to_dict()
        else:
            return None  # Usuário não encontrado
    except Exception as e:
        print(f"ERRO ao buscar usuário {matricula}: {e}")
        return None
