# Arquivo: routes/erp_routes.py

import random
from flask import Blueprint, request, jsonify, g
from firebase_admin import firestore
from datetime import datetime, timedelta  # Novo import para simulação de KPIs

# Importações CRÍTICAS das funções de serviço
from services.firestore_service import (
    get_db,
    log_auditoria,
    save_or_update_product,  # Nova Importação
    find_product_by_barcode  # Nova Importação
)
from services.integrations_service import IntegrationsService
from .auth_routes import auth_required  # Importa o decorator

# Define o Blueprint para as rotas do ERP
erp_bp = Blueprint('erp', __name__)


# ----------------------------------------------------------
# ROTA DE PRODUTOS (Módulo de Cadastro e Consulta)
# ----------------------------------------------------------

@erp_bp.route('/produtos/cadastrar', methods=['POST'])
@auth_required
def cadastrar_produto():
    """Endpoint para salvar ou atualizar dados de um produto."""
    data = request.get_json()
    barcode = data.get('codigoBarra')

    if not barcode or not data.get('nome'):
        log_auditoria(g.user_matricula, 'Produto', 'Erro Validação', 'Dados de cadastro incompletos.')
        return jsonify({"message": "Código de Barras e Nome são obrigatórios.", "success": False}), 400

    # Adiciona a matrícula do usuário que está fazendo o cadastro
    data['cadastrado_por'] = g.user_matricula

    # Chama o serviço para salvar/atualizar no Firestore
    success, message = save_or_update_product(data)

    if success:
        acao = "Atualização" if find_product_by_barcode(barcode) else "Cadastro"
        log_auditoria(g.user_matricula, 'Produto', acao, f"Produto {barcode} - {data.get('nome')}")
        return jsonify({"message": f"{acao} de produto bem-sucedido: {message}", "success": True}), 200
    else:
        log_auditoria(g.user_matricula, 'Produto', 'Erro DB', f"Falha ao salvar {barcode}: {message}")
        return jsonify({"message": f"Erro ao salvar produto: {message}", "success": False}), 500


@erp_bp.route('/produtos/buscar/<string:barcode>', methods=['GET'])
@auth_required
def buscar_produto(barcode):
    """Endpoint para buscar um produto pelo código de barras."""

    if not barcode:
        return jsonify({"message": "Código de Barras é obrigatório.", "success": False}), 400

    produto = find_product_by_barcode(barcode)

    if produto:
        # log_auditoria é opcional aqui, mas pode ser útil para monitorar o PDV
        return jsonify(produto), 200
    else:
        return jsonify({"message": "Produto não encontrado.", "success": False}), 404


# ----------------------------------------------------------
# ROTA DE RECEBIMENTO DE NF-e (Integração)
# ----------------------------------------------------------

@erp_bp.route('/recebimento/confirmar', methods=['POST'])
@auth_required
def confirmar_recebimento():
    """Endpoint para confirmar o recebimento de uma NF-e."""
    data = request.get_json()
    nf_numero = data.get('nf_numero')
    itens_nf = data.get('itens', [])

    if not nf_numero or not itens_nf:
        log_auditoria(g.user_matricula, 'Recebimento', 'Erro Validação', 'Dados de NF incompletos.')
        return jsonify({"message": "Dados de NF incompletos.", "success": False}), 400

    log_auditoria(g.user_matricula, 'Recebimento', 'Confirmação NF', f"NF {nf_numero} confirmada.")

    # Simulação das 3 ações cruciais no recebimento (Usando Firestore Service):
    db_instance = get_db()
    if db_instance:
        for item in itens_nf:
            barcode = item.get('codigoBarra')
            quantidade_recebida = item.get('quantidade')
            novo_custo_liquido = item.get('custo_unitario')

            if barcode:
                # 1. Atualizar Estoque e Custo Unitário (no Firestore)
                # Esta lógica deve ser refinada em um sistema real para garantir transacionalidade

                # Busca o produto atual para somar o estoque
                produto_atual = find_product_by_barcode(barcode)
                estoque_atual = produto_atual.get('estoque_atual', 0) if produto_atual else 0

                # Novo objeto de atualização
                update_data = {
                    'estoque_atual': estoque_atual + quantidade_recebida,
                    'custoLiquido': novo_custo_liquido,
                    'last_updated': firestore.SERVER_TIMESTAMP
                }

                # Assume que o produto já existe ou será criado/atualizado com o novo custo
                success, msg = save_or_update_product(update_data | item)  # Mescla dados da NF com atualização

                if not success:
                    print(f"AVISO: Falha ao atualizar produto {barcode} durante recebimento. {msg}")

    # 2. Gerar Título no Contas a Pagar (simulado)
    # Aqui, em um sistema real, você chamaria um serviço Financeiro.
    # IntegrationsService().gerar_titulo_a_pagar(...)

    # 3. Loga o Título (no Log de Auditoria)
    log_auditoria(g.user_matricula, 'Financeiro', 'Título Gerado', f"NF {nf_numero} - R$ {data.get('valor_total')}")

    return jsonify({
        "message": f"Recebimento da NF {nf_numero} concluído: Estoque e Custos atualizados, Título a Pagar gerado.",
        "success": True
    }), 200


# ----------------------------------------------------------
# ROTA DE ADMINISTRAÇÃO DE USUÁRIOS (RETA - Simulação)
# ----------------------------------------------------------

@erp_bp.route('/admin/usuarios', methods=['GET'])
@auth_required
def listar_usuarios():
    # Rota simulada para o módulo RETA (Administração de Usuários)

    # Simulação: Buscar usuários do banco (Aqui estamos simulando os dados)
    usuarios_simulados = [
        {"matricula": "ADMIN01", "nome": "Jéssica Admin", "acesso": "Admin"},
        {"matricula": "GERENTE01", "nome": "Roberto Gerente", "acesso": "Gerente"},
        {"matricula": "OP001", "nome": "Carlos Operador", "acesso": "Operador"},
    ]

    # No seu front-end (reta.html), você verificará a permissão, mas o backend também deve fazê-lo
    if g.user_permissao not in ['Admin', 'Gerente']:
        log_auditoria(g.user_matricula, 'RETA', 'Acesso Negado',
                      'Tentativa de listar usuários sem permissão Admin/Gerente.')
        return jsonify({"message": "Acesso negado. Requer permissão de Admin ou Gerente.", "success": False}), 403

    # Em um sistema real, buscaria da coleção 'usuarios'
    return jsonify(usuarios_simulados), 200


# ----------------------------------------------------------
# ROTA DE DASHBOARD (KPIs - Simulação)
# ----------------------------------------------------------

@erp_bp.route('/dashboard/kpis', methods=['GET'])
@auth_required
def get_kpis():
    """Fornece dados simulados para o Dashboard Gerencial."""

    # Acesso é restrito para Admin e Gerente (Conforme o front-end)
    if g.user_permissao not in ['Admin', 'Gerente']:
        return jsonify({"message": "Acesso negado ao Dashboard.", "success": False}), 403

    # --- SIMULAÇÃO DE DADOS EM TEMPO REAL ---

    # 1. Indicadores Financeiros (Valores altos, simulam o acumulado do dia)
    venda_bruta_hoje = round(random.uniform(5000.00, 15000.00), 2)
    margem_bruta_percentual = round(random.uniform(25.0, 35.0), 1)

    # 2. Indicadores Operacionais
    itens_ponto_pedido = random.randint(15, 30)
    estoque_total_valor = round(random.uniform(150000.00, 300000.00), 2)

    # 3. Auditoria Simulação (para a tabela de Auditoria no dashboard.html)
    # Gerar logs simulados de acessos e ações recentes (das últimas 2 horas)
    now = datetime.now()
    auditoria_logs = [
        {'usuario': 'ADMIN01', 'acesso': 'Admin', 'tempoLogado': '1:45', 'ultimaAcao': 'Consulta KPI'},
        {'usuario': 'GERENTE01', 'acesso': 'Gerente', 'tempoLogado': '2:10', 'ultimaAcao': 'Confirma NF 1234'},
        {'usuario': 'OP001', 'acesso': 'Operador', 'tempoLogado': '0:30', 'ultimaAcao': 'Venda #987'},
        {'usuario': 'OP002', 'acesso': 'Operador', 'tempoLogado': '1:00', 'ultimaAcao': 'Busca Produto'},
    ]

    return jsonify({
        "success": True,
        "kpis": {
            "venda_bruta_hoje": venda_bruta_hoje,
            "margem_bruta_percentual": margem_bruta_percentual,
            "itens_ponto_pedido": itens_ponto_pedido,
            "estoque_total_valor": estoque_total_valor,
        },
        "auditoria": auditoria_logs
    }), 200


# ----------------------------------------------------------
# ROTA DE FECHAMENTO DE VENDA (PDV)
# ----------------------------------------------------------

@erp_bp.route('/vendas/fechar', methods=['POST'])
@auth_required
def fechar_venda():
    """
    Endpoint CRÍTICO para fechar uma venda, incluindo Pagamento e NF-e.
    """
    db = get_db()
    data = request.get_json()

    # Validação inicial dos dados
    itens = data.get('itens', [])
    valor_total = data.get('valor_total')

    if not itens or not valor_total:
        log_auditoria(g.user_matricula, 'PDV', 'Erro Validação', 'Dados de venda incompletos.')
        return jsonify({"message": "Dados de venda incompletos.", "success": False}), 400

    # 1. INICIALIZA o serviço de integração
    integrations = IntegrationsService(g.user_matricula)

    # 2. PROCESSA o Pagamento
    dados_pagamento = data.get('dados_pagamento', {})
    pagamento_result = integrations.processar_pagamento(valor_total, dados_pagamento)

    if pagamento_result['status'] == 'NEGADO':
        return jsonify({"message": "Pagamento negado pelo Gateway.", "success": False}), 402

    # 3. REGISTRA a Venda no Banco de Dados (Firestore)
    venda_id = f"VENDA_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100, 999)}"

    venda_record = {
        'id_venda': venda_id,
        'timestamp': firestore.SERVER_TIMESTAMP,
        'matricula_operador': g.user_matricula,
        'valor_total': valor_total,
        'itens': itens,  # Itens da venda
        'status': 'APROVADA',
        'transacao_id': pagamento_result.get('transaction_id')
    }

    try:
        db.collection('vendas').document(venda_id).set(venda_record)
        log_auditoria(g.user_matricula, 'PDV', 'Venda Registrada', f"ID: {venda_id}")

        # 4. ATUALIZA Estoque e Loga no Log de Auditoria
        for item in itens:
            barcode = item.get('codigoBarra')
            quantidade_vendida = item.get('quantidade')

            # Atualização de Estoque (decremento) - Lógica de serviço de produto
            # Buscar produto atual
            produto_atual = find_product_by_barcode(barcode)
            if produto_atual:
                novo_estoque = max(0, produto_atual.get('estoque_atual', 0) - quantidade_vendida)

                # Chamar o serviço para atualizar o estoque
                update_data = {'estoque_atual': novo_estoque}
                save_or_update_product(update_data | item)  # Mescla dados e atualiza (Apenas o estoque mudou aqui)

            log_auditoria(g.user_matricula, 'Estoque', 'Saída Mercadoria', f"Produto {barcode} -{quantidade_vendida}un")

        # 5. EMITE a Nota Fiscal Eletrônica (NF-e)
        nfe_result = integrations.emitir_nfe(venda_record, itens)

        if nfe_result['status'] == 'AUTORIZADO':
            log_auditoria(g.user_matricula, 'Fiscal', 'NF-e Autorizada', f"Chave: {nfe_result['chave_acesso']}")
            db.collection('vendas').document(venda_id).update({
                'nfe_chave': nfe_result['chave_acesso'],
                'status': 'FINALIZADA'
            })
        else:
            # Caso de Contingência (emissão de Cupom Fiscal ou NF-e em contingência)
            log_auditoria(g.user_matricula, 'Fiscal', 'NF-e Falha', f"Venda {venda_id}")
            db.collection('vendas').document(venda_id).update({'status': 'CONTINGÊNCIA'})

        # SUCESSO FINAL
        return jsonify({
            "message": "Venda finalizada com sucesso! Pagamento Aprovado e NF-e Emitida.",
            "success": True,
            "venda_id": venda_id,
            "chave_nfe": nfe_result.get('chave_acesso', 'Contingência')
        }), 200

    except Exception as e:
        log_auditoria(g.user_matricula, 'PDV', 'Erro Crítico', f"Venda {venda_id} falhou: {e}")
        return jsonify({"message": f"Erro interno ao finalizar a venda: {e}", "success": False}), 500