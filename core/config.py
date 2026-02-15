import os
import pytz

# Carrega .env localmente (não commita este arquivo)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv opcional

# --- CREDENCIAIS (via variáveis de ambiente) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Configure SUPABASE_URL e SUPABASE_KEY em variáveis de ambiente ou no arquivo .env"
    )

FUSO_BR = pytz.timezone('America/Sao_Paulo')

# --- REGRAS DE NEGÓCIO (VALIDADE) ---
DIAS_ALERTA_AMARELO = 7  
DIAS_ALERTA_VERMELHO = 3 

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
    # Cores para alertas de validade
    "VALIDADE": {
        "CRITICO": "#ff4d4d", # Vermelho vivo
        "ALERTA": "#ffeb3b",  # Amarelo vivo
        "OK": ""              # Sem cor de fundo
    },
    # Cores usadas no tema da interface (CSS)
    "TEMA": {
        "Admin": {
            "principal": "#b10202",             # Vermelho JT
            "destaque": "#d9534f",              # Vermelho mais claro (Toasts/Alertas)
            "bg_card_sutil": "rgba(177, 2, 2, 0.1)" # Fundo translúcido avermelhado
        },
        "Operador": {
            "principal": "#001f3f",             # Azul Marinho
            "destaque": "#0074cc",              # Azul mais claro
            "bg_card_sutil": "rgba(0, 31, 63, 0.2)" # Fundo translúcido azulado
        }
    }
}