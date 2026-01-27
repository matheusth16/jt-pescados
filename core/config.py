import pytz

# --- CONSTANTES GERAIS ---
SHEET_ID = "1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc"
FUSO_BR = pytz.timezone('America/Sao_Paulo')

# --- LISTAS DE OPÇÕES (Dropdowns) ---
LISTA_STATUS = [
    "GERADO", "PENDENTE", "NÃO GERADO", 
    "CANCELADO", "ENTREGUE", "ORÇAMENTO", "RESERVADO"
]

LISTA_PAGAMENTO = [
    "A COMBINAR", "PIX", "BOLETO", "CARTÃO"
]

# --- DESIGN SYSTEM & CORES ---
PALETA_CORES = {
    # Cores usadas nos gráficos e status dos pedidos
    "STATUS": {
        "PENDENTE": "#ffeb00",     # Amarelo
        "GERADO": "#ff8500",       # Laranja
        "NÃO GERADO": "#b10202",   # Vermelho Escuro
        "CANCELADO": "#ffa0a0",    # Vermelho Claro
        "ENTREGUE": "#11734b",     # Verde
        "ORÇAMENTO": "#e8eaed",    # Cinza Claro
        "RESERVADO": "#0a53a8"     # Azul
    },
    # Cores usadas no tema da interface (CSS)
    "TEMA": {
        "Operador": {
            "principal": "#004080",       # Azul Marinho
            "destaque": "#00BFFF",        # Azul Ciano
            "bg_card_sutil": "rgba(0, 191, 255, 0.03)"
        },
        "Admin": {
            "principal": "#B22222",       # Vermelho JT
            "destaque": "#FFD700",        # Dourado
            "bg_card_sutil": "rgba(255, 0, 0, 0.03)"
        }
    }
}