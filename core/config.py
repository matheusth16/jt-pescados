import os
import pytz

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv opcional

# --- Tenta pegar credenciais também do Streamlit Secrets (Cloud) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

try:
    import streamlit as st
    # usa secrets como fallback se env vars não existirem
    SUPABASE_URL = SUPABASE_URL or st.secrets.get("SUPABASE_URL", None)
    SUPABASE_KEY = SUPABASE_KEY or st.secrets.get("SUPABASE_KEY", None)
except Exception:
    # streamlit pode não existir em alguns contextos (scripts, testes)
    pass

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Faltam credenciais do Supabase. Configure SUPABASE_URL e SUPABASE_KEY "
        "em variáveis de ambiente, no arquivo .env (local) ou em Secrets do Streamlit Cloud."
    )

FUSO_BR = pytz.timezone("America/Sao_Paulo")

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
    "STATUS": {
        "PENDENTE": "#ffeb00",
        "GERADO": "#ff8500",
        "NÃO GERADO": "#b10202",
        "CANCELADO": "#ffa0a0",
        "ENTREGUE": "#11734b",
        "ORÇAMENTO": "#e8eaed",
        "RESERVADO": "#0a53a8"
    },
    "VALIDADE": {
        "CRITICO": "#ff4d4d",
        "ALERTA": "#ffeb3b",
        "OK": ""
    },
    "TEMA": {
        "Admin": {
            "principal": "#b10202",
            "destaque": "#d9534f",
            "bg_card_sutil": "rgba(177, 2, 2, 0.1)"
        },
        "Operador": {
            "principal": "#001f3f",
            "destaque": "#0074cc",
            "bg_card_sutil": "rgba(0, 31, 63, 0.2)"
        }
    }
}
