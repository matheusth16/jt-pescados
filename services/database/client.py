"""
Cliente Supabase e funções base compartilhadas.
"""
import time
from supabase import create_client, Client
import streamlit as st

from core.config import SUPABASE_URL, SUPABASE_KEY


@st.cache_resource
def get_db_client() -> Client:
    """Retorna o cliente do Supabase (Singleton)."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_max_id(table_name: str, id_column: str) -> int:
    """Busca o maior ID numérico de uma tabela para simular auto-incremento manual."""
    try:
        client = get_db_client()
        response = client.table(table_name)\
            .select(id_column)\
            .order(id_column, desc=True)\
            .limit(1)\
            .execute()
        if response.data:
            return int(response.data[0][id_column])
        return 0
    except Exception:
        return 0


def obter_versao_planilha():
    """Controle de cache inteligente."""
    return time.time()
