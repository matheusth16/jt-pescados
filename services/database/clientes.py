"""
Operações de clientes.
"""
import pandas as pd
import streamlit as st

from services.database.client import get_db_client, get_max_id
from services.utils import limpar_texto


@st.cache_data(ttl=300, show_spinner=False)
def listar_clientes(_hash_versao=None):
    client = get_db_client()
    try:
        response = client.table("clientes").select("Cliente").order("Cliente").execute()
        if response.data:
            lista = [c["Cliente"] for c in response.data if c["Cliente"]]
            return sorted(list(set(lista)))
    except Exception:
        pass
    return []


def criar_novo_cliente(nome, cidade, documento=""):
    client = get_db_client()
    listar_clientes.clear()
    get_metricas.clear()

    nome_final = limpar_texto(nome)
    cidade_final = limpar_texto(cidade)
    doc_final = limpar_texto(documento)

    novo_id = get_max_id("clientes", "Código") + 1

    dados = {
        "Código": novo_id,
        "Cliente": nome_final,
        "Nome Cidade": cidade_final,
        "CPF/CNPJ": doc_final,
        "ROTA": "NÃO DEFINIDO",
        "PRAZO": "A VISTA"
    }

    try:
        client.table("clientes").insert(dados).execute()
    except Exception as e:
        st.error(f"Erro ao criar cliente: {e}")


@st.cache_data(ttl=300, show_spinner=False)
def get_metricas(_hash_versao=None):
    client = get_db_client()
    try:
        # Traz 1000 registros max - já basta para dashboard
        resp_cli = client.table("clientes").select("Código").limit(1000).execute()
        resp_ped = client.table("pedidos").select("ID_PEDIDO").limit(1000).execute()
        return len(resp_cli.data), len(resp_ped.data)
    except:
        return 0, 0


def buscar_clientes_paginado(pagina_atual=1, tamanho_pagina=20):
    client = get_db_client()
    inicio = (pagina_atual - 1) * tamanho_pagina
    fim = inicio + tamanho_pagina - 1

    try:
        cols = '"Código", Cliente, "Nome Cidade", "CPF/CNPJ", ROTA'
        response = client.table("clientes")\
            .select(cols, count="exact")\
            .order("Cliente", desc=False)\
            .range(inicio, fim)\
            .execute()

        total_registros = response.count if response.count is not None else 0
        df = pd.DataFrame(response.data)
        if df.empty:
            df = pd.DataFrame(columns=["Código", "Cliente", "Nome Cidade", "ROTA"])
        return df, total_registros
    except Exception as e:
        st.error(f"Erro clientes: {e}")
        return pd.DataFrame(), 0
