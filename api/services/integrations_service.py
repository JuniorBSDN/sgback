import requests
from config import Config
from services.firestore_service import log_auditoria


class IntegrationsService:
    """Encapsula a lógica de comunicação com Gateways de Pagamento e Emissores de NF-e."""

    def __init__(self, matricula_operador):
        self.matricula_operador = matricula_operador

    # Exemplo de Correção (dentro de IntegrationsService)

    def processar_pagamento(self, valor_total, dados_pagamento):
        # ... código de logs omitido ...

        # --- SUBSTITUIR SIMULAÇÃO POR CHAMADA REAL ---
        try:
            payload = {"valor": valor_total, "dados": dados_pagamento}
            # IMPORTANTE: Você precisará de 'requests' instalado (pip install requests)
            response = requests.post(Config.PAYMENT_GATEWAY_URL, json=payload, timeout=5)
            response.raise_for_status()  # Lança exceção para status 4xx/5xx

            # Analise a resposta real da API de Pagamento
            api_response = response.json()
            if api_response.get("status") == "APROVADO":
                # ... loga sucesso ...
                return {"status": "APROVADO", "transaction_id": api_response.get("id")}
            else:
                # ... loga falha ...
                return {"status": "NEGADO", "motivo": api_response.get("motivo")}

        except requests.exceptions.RequestException as e:
            # ... loga erro de conexão ou HTTP ...
            return {"status": "NEGADO", "motivo": f"Erro de conexão com o Gateway: {e}"}